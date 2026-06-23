"""Milvus 기반 다양성 큐레이션 — 임베딩 유사도로 redundant 를 솎아 '다양한 알짜'만 남긴다.

왜 (B안):
  순수 near-dup(cos>=0.95) 은 ~0.2% 로 적다. 하지만 비슷비슷한 문장이 뭉친
  '과대표집 클러스터'(같은 뉴스/위키 변형 다수)는 파인튜닝에 redundant 신호다.
  → 임베딩 + Milvus 유사검색으로 greedy 하게 "이미 비슷한 게 있으면 버림" =
     남는 건 서로 충분히 다른 다양한 대표들.

동작 (greedy diversity filter):
  컬렉션(=지금까지 남긴 대표들) 에 대해 각 후보의 최근접 유사도를 구해
  threshold 이상이면 redundant(drop), 아니면 keep + 컬렉션에 삽입.
  - cross-chunk(스케일): Milvus 유사검색 (수백만개도 ANN 으로 빠름)
  - within-chunk(정확): numpy (청크 ≤ 수천이라 저렴)

사용:
  cd C:\\My-AI-Security-Project\\PII\\ner
  python datacenter/diversity_curate.py --source weak --limit 20000 --threshold 0.92
  python datacenter/diversity_curate.py --source gold --threshold 0.95   # 전체

⚠️ Milvus(Docker) 가 떠 있어야 함: cd datacenter/milvus && docker compose up -d
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

import numpy as np

# Windows 콘솔(cp949)이 일부 유니코드(\xa0 등) 못 찍어 죽는 것 방지
try:
    import sys as _sys

    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DB = Path(__file__).resolve().parent / "ner_datacenter.db"
OUT_DIR = Path(__file__).resolve().parents[1] / "data"
TABLE = {"weak": "weak_examples", "gold": "ner_examples"}


def load_rows(source: str, limit: int | None):
    con = sqlite3.connect(DB)
    q = f"SELECT id, sentence, source FROM {TABLE[source]} WHERE length(sentence) BETWEEN 5 AND 300"
    if limit:
        q += f" LIMIT {limit}"
    rows = con.execute(q).fetchall()
    con.close()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["weak", "gold"], default="weak")
    ap.add_argument("--limit", type=int, default=20000, help="0=전체")
    ap.add_argument("--threshold", type=float, default=0.92, help="이 이상 유사하면 redundant")
    ap.add_argument("--model", default="paraphrase-multilingual-MiniLM-L12-v2")
    ap.add_argument("--collection", default="curate")
    ap.add_argument("--uri", default="http://localhost:19530")
    ap.add_argument("--chunk", type=int, default=2000)
    a = ap.parse_args()

    rows = load_rows(a.source, a.limit or None)
    ids = [int(r[0]) for r in rows]
    sents = [r[1] for r in rows]
    n = len(sents)
    print(f"[load] 후보 {n:,} ({a.source}), threshold={a.threshold}")

    # 1) 임베딩 (캐시 — 같은 source/limit/model 이면 재계산 안 함, threshold 튜닝 빠르게)
    OUT_DIR.mkdir(exist_ok=True)
    ck = OUT_DIR / f"_embcache_{a.source}_{a.limit}_{a.model.replace('/','_')}.npy"
    cki = ck.with_suffix(".ids.json")
    emb = None
    if ck.exists() and cki.exists() and json.loads(cki.read_text()) == ids:
        emb = np.load(ck)
        print(f"[embed] 캐시 로드 {emb.shape}")
    if emb is None:
        from sentence_transformers import SentenceTransformer

        t = time.time()
        model = SentenceTransformer(a.model)
        emb = model.encode(
            sents, batch_size=64, normalize_embeddings=True, show_progress_bar=True
        ).astype("float32")
        print(f"[embed] {emb.shape} in {time.time()-t:.0f}s")
        np.save(ck, emb)
        cki.write_text(json.dumps(ids))
    dim = int(emb.shape[1])

    # 2) Milvus 컬렉션 (대표 금고)
    from pymilvus import MilvusClient

    client = MilvusClient(uri=a.uri)
    if client.has_collection(a.collection):
        client.drop_collection(a.collection)
    client.create_collection(
        a.collection, dimension=dim, metric_type="COSINE", auto_id=False
    )

    kept_ids: list[int] = []
    dropped: list[tuple[int, float]] = []  # (id, nearest_sim)
    t = time.time()

    for start in range(0, n, a.chunk):
        cv = emb[start : start + a.chunk]
        cids = ids[start : start + a.chunk]

        # cross-chunk: Milvus 에서 기존 대표 중 최근접 유사도
        if kept_ids:
            res = client.search(a.collection, data=cv.tolist(), limit=1)
            near = [(h[0]["distance"] if h else -1.0) for h in res]  # COSINE: 클수록 유사
        else:
            near = [-1.0] * len(cv)

        # within-chunk greedy (numpy, 정확)
        keep_k = []
        chunk_mat = np.zeros((0, dim), dtype="float32")
        for k in range(len(cv)):
            s = near[k]
            if s < a.threshold and chunk_mat.shape[0]:
                s = max(s, float((chunk_mat @ cv[k]).max()))
            if s >= a.threshold:
                dropped.append((cids[k], float(s)))
            else:
                keep_k.append(k)
                chunk_mat = np.vstack([chunk_mat, cv[k][None, :]])

        if keep_k:
            client.insert(
                a.collection,
                [{"id": cids[k], "vector": cv[k].tolist()} for k in keep_k],
            )
            kept_ids.extend(cids[k] for k in keep_k)
        client.flush(a.collection)  # 다음 청크 검색에 보이게
        print(
            f"  [{min(start+a.chunk,n):>7,}/{n:,}] kept={len(kept_ids):,} "
            f"dropped={len(dropped):,} ({time.time()-t:.0f}s)",
            flush=True,
        )

    # 3) 결과
    kept = len(kept_ids)
    drop = len(dropped)
    print("\n===== 큐레이션 결과 =====")
    print(f"  후보:     {n:,}")
    print(f"  알짜 keep: {kept:,} ({kept/n*100:.1f}%)")
    print(f"  redundant: {drop:,} ({drop/n*100:.1f}%)  ← 다양성 위해 솎아냄")

    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"curated_{a.source}_t{a.threshold}.json"
    out.write_text(
        json.dumps(
            {"source": a.source, "threshold": a.threshold, "n": n, "kept_ids": kept_ids},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"  → 알짜 id 저장: {out}")

    if dropped:
        ex = sorted(dropped, key=lambda x: -x[1])[:3]
        idmap = {ids[i]: sents[i] for i in range(n)}
        print("\n  솎인 예시(가장 유사한 3):")
        for did, s in ex:
            print(f"    sim={s:.3f}  {idmap.get(did,'')[:80]}")


if __name__ == "__main__":
    main()
