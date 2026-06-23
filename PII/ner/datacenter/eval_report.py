"""팀원 평가용 리포트 생성 — DB 16GB 안 옮기고 평가 가능하게.

생성물 (datacenter/eval_package/):
  EVAL_REPORT.md        — 수치/라이선스/누설/분리/엔티티 분포 종합 (팀원이 읽는 본문)
  samples_gold.jsonl    — gold 무작위 샘플 N (라벨 복원해 눈으로 검수)
  samples_weak.jsonl    — weak 소스별 무작위 샘플 (품질 검수)

팀원 사용:
  python datacenter/eval_report.py        # 리포트+샘플 생성
  → eval_package/ 폴더만 받아서 EVAL_REPORT.md 읽고 samples_*.jsonl 검수
  (직접 재현하려면 run_collectors.py --stats / leakage_gate.py / source_ablation.py 실행)
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import DB_PATH  # noqa: E402

OUT = Path(__file__).resolve().parent / "eval_package"
SAMPLE_PER_SOURCE = 8


def _reconstruct(tokens: list[str], labels: list[str]) -> list[dict]:
    ents, cur = [], None
    for t, l in zip(tokens, labels):
        if l.startswith("B-"):
            cur = {"text": t, "type": l[2:]}
            ents.append(cur)
        elif l.startswith("I-") and cur:
            cur["text"] += t
        else:
            cur = None
    return ents


def main() -> None:
    OUT.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    L: list[str] = ["# NER 데이터센터 평가 리포트 (팀원용)", ""]
    L.append("> DB 16GB 미전송. 본 리포트 + samples_*.jsonl 로 평가. 재현은 §재현 참조.\n")

    # 1. 총괄
    g = conn.execute("SELECT COUNT(*) FROM ner_examples").fetchone()[0]
    wd, ws = conn.execute("SELECT COUNT(*),SUM(n_spans) FROM weak_examples").fetchone()
    gz = conn.execute("SELECT COUNT(*) FROM gazetteers").fetchone()[0]
    db_gb = DB_PATH.stat().st_size / 1e9
    L += ["## 1. 총괄", "",
          f"- gold(학습 후보) ner_examples: **{g:,}** 문장",
          f"- weak(PSEUDO, 격리): **{wd:,}** 문서 / **{ws:,}** PII span",
          f"- gazetteer: **{gz:,}**", f"- DB: {db_gb:.1f} GB", ""]

    # 2. gold 라이선스 (진짜 학습가능 얼마)
    L += ["## 2. gold 라이선스별 (★ 진짜 학습/공개 가능 = CC-BY-SA만)", "",
          "| license | 문장 | 학습 투입 |", "|---|---:|---|"]
    note = {"CC-BY-SA-4.0": "✅ 바로 가능(공개 안전)",
            "AIHub-derived (재배포 확인필요)": "⚠️ ablation+라이선스 확인 후",
            "word-level (조사오염 위험·ablation 필수)": "⚠️ 단독 ablation 통과 후"}
    for lic, n in conn.execute("SELECT license,COUNT(*) FROM ner_examples GROUP BY license ORDER BY 2 DESC"):
        L.append(f"| {lic} | {n:,} | {note.get(lic,'?')} |")
    L.append("")

    # 3. weak 도메인별
    L += ["## 3. weak 도메인별 (PSEUDO — 학습 직접 투입 X, 검수/ablation 후보)", "",
          "| source | 문서 | span |", "|---|---:|---:|"]
    for s, n, sp in conn.execute("SELECT source,COUNT(*),SUM(n_spans) FROM weak_examples GROUP BY source ORDER BY 2 DESC"):
        L.append(f"| {s} | {n:,} | {sp or 0:,} |")
    L.append("")

    # 4. gazetteer
    L += ["## 4. gazetteer", "", "| type | 개수 |", "|---|---:|"]
    for et, n in conn.execute("SELECT entity_type,COUNT(*) FROM gazetteers GROUP BY entity_type"):
        L.append(f"| {et} | {n:,} |")
    L.append("")

    # 5. gold/weak 분리 증명 (해시 교집합 0이어야)
    gold_h = {h for (h,) in conn.execute("SELECT content_hash FROM ner_examples")}
    weak_h = {h for (h,) in conn.execute("SELECT content_hash FROM weak_examples")}
    inter = len(gold_h & weak_h)
    L += ["## 5. gold/weak 분리 증명", "",
          f"- gold 고유 문장 hash: {len(gold_h):,}",
          f"- weak 고유 문장 hash: {len(weak_h):,}",
          f"- **교집합(weak가 gold 오염): {inter}** {'✅ 0=분리 정상' if inter==0 else '🚨 오염!'}", ""]

    # 6. 엔티티 분포
    L += ["## 6. 엔티티 분포 (gold 라벨 기준 샘플 추정)", ""]
    L.append("gold/weak 의 타입별 span 은 §3 + samples 로 확인. weak 는 확장태그(DISEASE 등) 포함.\n")

    # 7. 누설 게이트
    try:
        from leakage_gate import run as leak_run
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = leak_run()
        L += ["## 7. 누설 게이트 (KLUE test 오염)", "",
              f"- 적재 {res['loaded']:,} vs KLUE test {res['eval_size']:,}",
              f"- **누설 {res['total_leaks']}건** {'✅' if res['total_leaks']==0 else '⚠️ 학습 전 제거 필요'}",
              f"- 소스별: {res['by_source']}", ""]
    except Exception as e:
        L += ["## 7. 누설 게이트", "", f"(직접 실행: `python datacenter/leakage_gate.py`) — {e}", ""]

    # 8. 재현 방법
    L += ["## 재현 (팀원이 직접 확인)", "",
          "```bash", "python datacenter/run_collectors.py --stats   # 전체 카운트",
          "python datacenter/leakage_gate.py              # 누설",
          "python datacenter/source_ablation.py           # 소스별 엔티티 기여+누설",
          "python datacenter/export_clean.py              # 깨끗한 학습셋 export",
          "```",
          "raw 데이터는 INVENTORY.md 출처. 코드는 datacenter/ (collector별 1파일).", ""]

    (OUT / "EVAL_REPORT.md").write_text("\n".join(L), encoding="utf-8")

    # 샘플 export (gold)
    with open(OUT / "samples_gold.jsonl", "w", encoding="utf-8") as f:
        for src in [r[0] for r in conn.execute("SELECT DISTINCT source FROM ner_examples")]:
            for toks_j, labs_j, sent in conn.execute(
                "SELECT tokens_json,label_names_json,sentence FROM ner_examples WHERE source=? "
                "ORDER BY id LIMIT ?", (src, SAMPLE_PER_SOURCE)):
                toks, labs = json.loads(toks_j), json.loads(labs_j)
                f.write(json.dumps({"source": src, "sentence": sent[:200],
                                    "entities": _reconstruct(toks, labs)}, ensure_ascii=False) + "\n")
    # 샘플 export (weak, 소스별)
    with open(OUT / "samples_weak.jsonl", "w", encoding="utf-8") as f:
        for src in [r[0] for r in conn.execute("SELECT DISTINCT source FROM weak_examples")]:
            for toks_j, labs_j, sent in conn.execute(
                "SELECT tokens_json,label_names_json,sentence FROM weak_examples WHERE source=? "
                "ORDER BY id LIMIT ?", (src, SAMPLE_PER_SOURCE)):
                toks, labs = json.loads(toks_j), json.loads(labs_j)
                f.write(json.dumps({"source": src, "sentence": sent[:200],
                                    "entities": _reconstruct(toks, labs)}, ensure_ascii=False) + "\n")

    conn.close()
    print(f"생성 완료 → {OUT}/")
    print("  EVAL_REPORT.md / samples_gold.jsonl / samples_weak.jsonl")


if __name__ == "__main__":
    main()
