"""NER 데이터센터 통합 러너 — collector 등록/실행.

finence/datacenter/run_collectors.py 패턴. 각 collector 는 collectors/<id>.py
모듈이고 collect(limit) 와 META 를 제공한다.

사용 (PowerShell):
  cd C:\\My-AI-Security-Project\\PII\\ner
  python datacenter/run_collectors.py                  # 전체
  python datacenter/run_collectors.py --only corpus4everyone
  python datacenter/run_collectors.py --limit 5000     # 소스별 상한 (빠른 검증)
  python datacenter/run_collectors.py --stats          # 적재 현황만

⚠️ v2 교훈: 수집 != 학습 투입. 새 소스는 leakage_gate.py 통과 + 소스별
   고정 KLUE val ablation 후에만 학습에 넣는다. 데이터센터는 "후보 금고".
"""
from __future__ import annotations

import argparse
import importlib
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db  # noqa: E402

# 등록된 collector (id = collectors/<id>.py). 새 소스는 여기에 추가.
REGISTRY = [
    "corpus4everyone",   # examples — KLUE 파생 char-level NER 117k (Phase A 메인)
    "open_ner_aihub",    # examples — AIHub 파생 span 119k (ORG/NAME 보강, 라이선스 분리)
    "kimmeoungjun_ner",  # examples — 단어단위 CoNLL 90k (🚨v2 위험, 격리 license)
    "org_krx",           # gazetteer — KRX 상장사 ORG 풀 2,765
    "ziozzang_address",  # gazetteer — 도로명 136k (ADDRESS 슬롯 다양화)
    "korea_admin",       # gazetteer — 행정구역 시도/구군+조합 (ADDRESS)
    "daje_address",      # gazetteer — 실제 전체주소 3.4k (ADDRESS, 건물+동/호)
    "name_gazetteer",    # gazetteer — gold NAME span 추출 + 성씨 (상용급 NAME 풀)
    "synth_conv_name",   # examples(GOLD) — 대화체 NAME 합성 (검증 갭#1 직격, 완벽 라벨)
    "ducut91_weak",      # weak_examples — Phase B 의료분쟁 텍스트형 PII (본문전체, PSEUDO)
    "news_rss",          # weak_examples — 뉴스 본문전체 라이브 스크래핑 (incremental 누적)
    "news91_weak",       # weak_examples — 91veMe 뉴스문어체 281k (샘플 weak)
    "privacy_weak",      # weak_examples — scvcoder 개인정보 상담/질의응답 (본문전체)
    "medical_qa_weak",   # weak_examples — hcw0329 의료 Q&A 15k
    "dialogue_weak",     # weak_examples — nayohan 페르소나 대화 76k (샘플)
    "sieu_news_weak",    # weak_examples — sieu-n 뉴스덤프 본문전체 (스트리밍, cap 10k)
    # 다양한 도메인 (상용급 다양성) — 2026-06-04
    "wiki_weak",         # weak_examples — 위키 본문전체 (인명/기관/지명 다양성 최고)
    "namuwiki_weak",     # weak_examples — 나무위키 문장 (대중문화 인명)
    "financial_weak",    # weak_examples — 금융 도메인 (BOK/한경)
    "review_weak",       # weak_examples — 리뷰 구어체 (스타일 다양성)
    "gov_ordinance_weak",# weak_examples — 행정 조례 문어체
    "textbook_weak",     # weak_examples — 교육 텍스트 (maywell 교과서)
    "korquad_chat_weak", # weak_examples — QA 대화
    "safe_conv_weak",    # weak_examples — 안전 대화
    "naver_news_weak",   # weak_examples — 네이버 뉴스요약 본문
]


def _run_one(conn, collector_id: str, limit: int, refresh: bool = False) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    mod = importlib.import_module(f"collectors.{collector_id}")
    license = mod.META.get("license", "unknown")
    try:
        # ⚠️ collect 를 먼저 (성공해야 purge). 예전엔 purge 가 먼저라 collect 가
        #    중간에 죽으면 그 소스가 통째로 비었다(wiki_weak 515k 손실 사고).
        result = mod.collect(limit=limit)
        kind = result.get("kind")
        if refresh:
            purged = db.delete_source(conn, collector_id)
            n_purged = sum(purged.values())
            if n_purged:
                print(f"  [refresh] {collector_id}: 기존 {n_purged} 행 purge {purged}", flush=True)
        if kind == "examples":
            counts = db.insert_examples(
                conn, collector_id, result["license"], result["examples"],
                split_hint=result.get("split_hint", "unknown"),
            )
        elif kind == "gazetteer":
            counts = db.insert_gazetteer(
                conn, result["entity_type"], result["values"],
                collector_id, result["license"],
            )
        elif kind == "weak_examples":
            counts = db.insert_weak_examples(
                conn, collector_id, result["license"], result["examples"]
            )
        else:
            raise ValueError(f"알 수 없는 collector kind: {kind}")
        db.record_run(conn, collector_id, license, started, "ok", counts)
        return {"id": collector_id, "kind": kind, "status": "ok", **counts}
    except Exception as exc:  # noqa: BLE001 — 한 collector 실패가 전체를 막지 않게
        db.record_run(conn, collector_id, license, started, "error", {}, error=str(exc))
        traceback.print_exc()
        return {"id": collector_id, "status": "error", "error": str(exc)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="쉼표구분 collector id (예: corpus4everyone)")
    ap.add_argument("--limit", type=int, default=0, help="소스별 example 상한 (0=전체)")
    ap.add_argument("--stats", action="store_true", help="적재 현황만 출력")
    ap.add_argument("--refresh", action="store_true",
                    help="재적재 전 해당 source 기존 행 purge (collector 정제 fix 반영용)")
    args = ap.parse_args()

    conn = db.connect()

    if args.stats:
        _print_stats(conn)
        return

    targets = args.only.split(",") if args.only else REGISTRY
    mode = " [refresh]" if args.refresh else ""
    print(f"[데이터센터] {len(targets)} collector 실행 (limit={args.limit or '전체'}){mode}\n")
    results = [_run_one(conn, cid.strip(), args.limit, refresh=args.refresh) for cid in targets]

    print("\n=== 실행 요약 ===")
    for r in results:
        if r.get("status") == "ok" and r.get("kind") == "examples":
            print(f"  {r['id']:20} examples  +{r['n_inserted']:>6} 신규 / "
                  f"{r['n_dup']:>6} 중복 / {r['n_invalid']:>4} 무효 (총 {r['n_seen']})")
        elif r.get("status") == "ok" and r.get("kind") == "weak_examples":
            print(f"  {r['id']:20} weak       +{r['n_inserted']:>6} 신규 / {r['n_dup']:>6} 중복 / "
                  f"{r.get('n_spans', 0):>6} span (PSEUDO)")
        elif r.get("status") == "ok":
            print(f"  {r['id']:20} gazetteer +{r['n_inserted']:>6} 신규 / {r['n_dup']:>6} 중복")
        else:
            print(f"  {r['id']:20} ERROR: {r.get('error')}")

    _print_stats(conn)


def _print_stats(conn) -> None:
    s = db.stats(conn)
    print(f"\n=== 적재 현황 (ner_datacenter.db) ===")
    print(f"  ner_examples 총 {s['total_examples']:,}")
    for source, n, ents in s["by_source"]:
        print(f"    - {source:20} {n:>7,} 문장 / {ents or 0:>7,} entity")
    print("  라이선스별:")
    for lic, n in s["by_license"]:
        print(f"    - {lic:20} {n:>7,}")
    if s["gazetteers"]:
        print("  gazetteers:")
        for etype, n in s["gazetteers"]:
            print(f"    - {etype:20} {n:>7,}")
    weak = db.weak_stats(conn)
    if weak:
        print("  weak_examples (Phase B PSEUDO — 텍스트형 PII 수확, gold 미포함):")
        for etype, n in weak:
            print(f"    - {etype:20} {n:>7,} span")


if __name__ == "__main__":
    main()
