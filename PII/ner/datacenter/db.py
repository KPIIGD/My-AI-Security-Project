"""NER 데이터센터 통합 DB (ner_datacenter.db).

finence/datacenter/db.py 패턴 차용:
  - content_hash UNIQUE 로 dedup (소스 간 중복/누설 차단)
  - collector_runs 로 실행 추적 (건수·중복·에러·라이선스)
  - INSERT OR IGNORE (첫 라벨링 보존; 동일 문장 다른 라벨은 disagreement = TODO 플래그)

NER 전용 추가:
  - license 컬럼 (졸업 후 공개용 — CC-BY-SA 깨끗한 것만 추리기)
  - gazetteers 테이블 (ORG/ADDRESS 풀 — 합성 슬롯 다양화용 resource)
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from schema import content_hash, count_entities, validate_example

DB_PATH = Path(__file__).resolve().parent / "ner_datacenter.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS ner_examples (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT NOT NULL UNIQUE,      -- 문장 기반 dedup 키
    source       TEXT NOT NULL,             -- collector id
    license      TEXT NOT NULL,             -- 라이선스 (공개 필터용)
    split_hint   TEXT,                      -- 소스 native split (train/val/test/unknown)
    sentence     TEXT NOT NULL,
    tokens_json  TEXT NOT NULL,             -- list[str]
    labels_json  TEXT NOT NULL,             -- list[int] (LABEL2ID)
    label_names_json TEXT NOT NULL,         -- list[str]
    n_tokens     INTEGER NOT NULL,
    n_entities   INTEGER NOT NULL,
    collected_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_examples_source ON ner_examples(source);
CREATE INDEX IF NOT EXISTS idx_examples_license ON ner_examples(license);

CREATE TABLE IF NOT EXISTS gazetteers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type  TEXT NOT NULL,             -- ORG / ADDRESS / NAME
    value        TEXT NOT NULL,
    source       TEXT NOT NULL,
    license      TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    UNIQUE(entity_type, value)
);
CREATE INDEX IF NOT EXISTS idx_gaz_type ON gazetteers(entity_type);

-- Phase B 약한 라벨링 트랙 (PSEUDO). gold ner_examples 와 절대 안 섞임.
-- 본문 전체 + regex/사전/gazetteer 자동 태깅 → 검수 후에만 학습 후보 승격.
CREATE TABLE IF NOT EXISTS weak_examples (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT NOT NULL UNIQUE,
    source       TEXT NOT NULL,
    license      TEXT NOT NULL,             -- PSEUDO-weak (검수필요)
    sentence     TEXT NOT NULL,             -- 본문 전체
    tokens_json  TEXT NOT NULL,
    label_names_json TEXT NOT NULL,         -- 확장 태그 (텍스트형 PII 포함)
    tag_set      TEXT NOT NULL,             -- 등장한 타입 (쉼표구분)
    n_tokens     INTEGER NOT NULL,
    n_spans      INTEGER NOT NULL,
    needs_review INTEGER DEFAULT 1,
    collected_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_weak_source ON weak_examples(source);

CREATE TABLE IF NOT EXISTS collector_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    status      TEXT,                        -- ok / error
    license     TEXT,
    n_seen      INTEGER DEFAULT 0,
    n_inserted  INTEGER DEFAULT 0,
    n_dup       INTEGER DEFAULT 0,
    n_invalid   INTEGER DEFAULT 0,
    error       TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.executescript(SCHEMA)
    return conn


def insert_examples(
    conn: sqlite3.Connection,
    source: str,
    license: str,
    examples: list[dict],
    *,
    split_hint: str = "unknown",
) -> dict:
    """example 리스트 삽입. content_hash 중복은 스킵. 무효는 거부.

    return: {n_seen, n_inserted, n_dup, n_invalid}.
    """
    n_seen = n_inserted = n_dup = n_invalid = 0
    now = _now()
    cur = conn.cursor()
    for ex in examples:
        n_seen += 1
        ok, _reason = validate_example(ex)
        if not ok:
            n_invalid += 1
            continue
        chash = content_hash(ex["sentence"])
        try:
            cur.execute(
                """INSERT INTO ner_examples
                   (content_hash, source, license, split_hint, sentence,
                    tokens_json, labels_json, label_names_json,
                    n_tokens, n_entities, collected_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    chash, source, license, split_hint, ex["sentence"],
                    json.dumps(ex["tokens"], ensure_ascii=False),
                    json.dumps(ex["labels"]),
                    json.dumps(ex["label_names"], ensure_ascii=False),
                    len(ex["tokens"]), count_entities(ex["label_names"]), now,
                ),
            )
            if cur.rowcount == 1:
                n_inserted += 1
            else:
                n_dup += 1
        except sqlite3.IntegrityError:
            n_dup += 1
    conn.commit()
    return {"n_seen": n_seen, "n_inserted": n_inserted, "n_dup": n_dup, "n_invalid": n_invalid}


def delete_source(conn: sqlite3.Connection, source: str) -> dict:
    """한 collector 의 기존 적재분을 전 트랙에서 삭제 (refresh 재적재용).

    content_hash UNIQUE + INSERT OR IGNORE 라 collector 코드를 고쳐도 기존 행은
    안 바뀐다. 정제 fix 를 금고에 반영하려면 purge 후 재수집해야 한다.
    한 source 는 한 트랙에만 살지만 안전하게 3 테이블 모두 삭제.
    """
    cur = conn.cursor()
    n_ex = cur.execute("DELETE FROM ner_examples WHERE source=?", (source,)).rowcount
    n_gaz = cur.execute("DELETE FROM gazetteers WHERE source=?", (source,)).rowcount
    n_weak = cur.execute("DELETE FROM weak_examples WHERE source=?", (source,)).rowcount
    conn.commit()
    return {"ner_examples": n_ex, "gazetteers": n_gaz, "weak_examples": n_weak}


def insert_gazetteer(
    conn: sqlite3.Connection, entity_type: str, values: list[str], source: str, license: str
) -> dict:
    """ORG/ADDRESS/NAME 풀 삽입 (합성 슬롯 다양화용). 중복 value 스킵."""
    n_seen = n_inserted = n_dup = 0
    now = _now()
    cur = conn.cursor()
    for value in values:
        value = (value or "").strip()
        if not value:
            continue
        n_seen += 1
        cur.execute(
            "INSERT OR IGNORE INTO gazetteers (entity_type, value, source, license, collected_at) VALUES (?,?,?,?,?)",
            (entity_type, value, source, license, now),
        )
        if cur.rowcount == 1:
            n_inserted += 1
        else:
            n_dup += 1
    conn.commit()
    return {"n_seen": n_seen, "n_inserted": n_inserted, "n_dup": n_dup}


def insert_weak_examples(
    conn: sqlite3.Connection, source: str, license: str, examples: list[dict]
) -> dict:
    """Phase B 약한 라벨 example 삽입 (weak_examples). content_hash 중복 스킵.

    example = {tokens, label_names, sentence}. 확장 태그 허용(텍스트형 PII).
    return: {n_seen, n_inserted, n_dup, n_spans}.
    """
    n_seen = n_inserted = n_dup = n_spans = 0
    now = _now()
    cur = conn.cursor()
    for ex in examples:
        n_seen += 1
        label_names = ex["label_names"]
        spans = sum(1 for label in label_names if label.startswith("B-"))
        tag_set = sorted({label[2:] for label in label_names if label != "O"})
        chash = content_hash(ex["sentence"])
        try:
            cur.execute(
                """INSERT INTO weak_examples
                   (content_hash, source, license, sentence, tokens_json,
                    label_names_json, tag_set, n_tokens, n_spans, needs_review, collected_at)
                   VALUES (?,?,?,?,?,?,?,?,?,1,?)""",
                (chash, source, license, ex["sentence"],
                 json.dumps(ex["tokens"], ensure_ascii=False),
                 json.dumps(label_names, ensure_ascii=False),
                 ",".join(tag_set), len(ex["tokens"]), spans, now),
            )
            if cur.rowcount == 1:
                n_inserted += 1
                n_spans += spans
            else:
                n_dup += 1
        except sqlite3.IntegrityError:
            n_dup += 1
    conn.commit()
    return {"n_seen": n_seen, "n_inserted": n_inserted, "n_dup": n_dup, "n_spans": n_spans}


def weak_stats(conn: sqlite3.Connection) -> list:
    """weak_examples 의 타입별 span 집계 (텍스트형 PII 수확량)."""
    rows = conn.execute("SELECT label_names_json FROM weak_examples").fetchall()
    counts: dict[str, int] = {}
    for (labs_json,) in rows:
        for label in json.loads(labs_json):
            if label.startswith("B-"):
                counts[label[2:]] = counts.get(label[2:], 0) + 1
    return sorted(counts.items(), key=lambda x: -x[1])


def record_run(conn: sqlite3.Connection, source: str, license: str, started_at: str,
               status: str, counts: dict, error: str | None = None) -> None:
    conn.execute(
        """INSERT INTO collector_runs
           (source, started_at, finished_at, status, license, n_seen, n_inserted, n_dup, n_invalid, error)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (source, started_at, _now(), status, license,
         counts.get("n_seen", 0), counts.get("n_inserted", 0),
         counts.get("n_dup", 0), counts.get("n_invalid", 0), error),
    )
    conn.commit()


def stats(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM ner_examples").fetchone()[0]
    by_source = cur.execute(
        "SELECT source, COUNT(*), SUM(n_entities) FROM ner_examples GROUP BY source ORDER BY 2 DESC"
    ).fetchall()
    by_license = cur.execute(
        "SELECT license, COUNT(*) FROM ner_examples GROUP BY license ORDER BY 2 DESC"
    ).fetchall()
    gaz = cur.execute(
        "SELECT entity_type, COUNT(*) FROM gazetteers GROUP BY entity_type"
    ).fetchall()
    return {"total_examples": total, "by_source": by_source, "by_license": by_license, "gazetteers": gaz}


def export_training_json(conn: sqlite3.Connection, out_path: Path, *,
                         licenses: list[str] | None = None,
                         exclude_hashes: set[str] | None = None) -> int:
    """ner_examples → 학습 포맷 JSON.

    - licenses: 지정 시 그 라이선스만 (공개 필터 — 졸업 공개용 CC-BY-SA 등).
    - exclude_hashes: 지정 시 그 content_hash 는 제외 (누설 문장 제거).

    출력 = list[{tokens, labels, label_names, sentence, source}] (data_prep 포맷과 동일).
    """
    cur = conn.cursor()
    if licenses:
        placeholders = ",".join("?" * len(licenses))
        rows = cur.execute(
            f"SELECT content_hash, tokens_json, labels_json, label_names_json, sentence, source "
            f"FROM ner_examples WHERE license IN ({placeholders})", licenses
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT content_hash, tokens_json, labels_json, label_names_json, sentence, source "
            "FROM ner_examples"
        ).fetchall()
    exclude = exclude_hashes or set()
    out = [
        {
            "tokens": json.loads(r[1]), "labels": json.loads(r[2]),
            "label_names": json.loads(r[3]), "sentence": r[4], "source": r[5],
        }
        for r in rows
        if r[0] not in exclude
    ]
    out_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return len(out)
