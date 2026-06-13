"""2인 독립 라벨 시트 생성 — candidates.jsonl → annotator_A / annotator_B.

검증 지적 대응: in-domain 평가셋은 사람 2인이 **독립**으로 라벨 후 조정해야 신뢰.
같은 후보를 두 시트로 복제(민우 / 양유상). 각자 채운 뒤 reconcile.py 로 합침.

라벨 방식 (사람 친화 인라인 마크업):
  원문:  홍길동님 삼성전자에 다녀요
  라벨:  {{NAME|홍길동}}님 {{ORG|삼성전자}}에 다녀요
  → NAME/ADDRESS/ORG 를 {{TYPE|텍스트}} 로 감싼다. 조사/호칭은 밖에.
  (라벨 기준은 LABEL_GUIDE_eval.md = label_guide_v1.md 따름)

구조형 PII 합성(synth_structured)은 정답이 이미 있어 사람 라벨 제외 — NER 7-way 밖.

사용:
  python eval_indomain/make_annotation_sheets.py
  → annotator_A.jsonl, annotator_B.jsonl (둘 다 동일 후보, annotation 필드 비어있음)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_GUIDE = "NAME/ADDRESS/ORG 를 {{TYPE|텍스트}} 로 감싸기. 조사·호칭·직책은 밖에. (LABEL_GUIDE_eval.md)"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default=str(_HERE / "candidates.jsonl"))
    ap.add_argument("--annotators", default="A,B", help="쉼표구분 라벨러 (예: minwoo,yangyusang)")
    args = ap.parse_args()

    cand_path = Path(args.candidates)
    if not cand_path.exists():
        raise SystemExit(f"후보 없음: {cand_path} — build_candidates.py 먼저 실행")
    cands = [json.loads(l) for l in cand_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    human = [c for c in cands if c.get("needs_human_label")]

    for who in args.annotators.split(","):
        who = who.strip()
        out = _HERE / f"annotator_{who}.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for c in human:
                f.write(json.dumps({
                    "id": c["id"],
                    "source": c["source"],
                    "sentence": c["sentence"],
                    "annotation": c["sentence"],  # ← 여기를 {{TYPE|텍스트}} 로 직접 편집
                    "_guide": _GUIDE,
                }, ensure_ascii=False) + "\n")
        print(f"  {out.name}: {len(human)} 문장 (annotation 필드 편집)")
    print(f"\n  사람 라벨 대상: {len(human)} / 전체 {len(cands)} (구조형 {len(cands)-len(human)}는 자동정답)")
    print(f"  두 라벨러가 각자 파일을 채운 뒤: python eval_indomain/reconcile.py")


if __name__ == "__main__":
    main()
