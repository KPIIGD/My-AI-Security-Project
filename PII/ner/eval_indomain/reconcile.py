"""2인 라벨 조정 — IAA(라벨러 간 일치도) + 불일치 추출 + 최종 gold.

워크플로우:
  1. annotator_A/B 가 {{TYPE|텍스트}} 마크업으로 각자 라벨
  2. 본 스크립트가: 마크업 파싱 → span / 원문 무결성 검사 /
     span-exact 일치도(F1·일치율) 계산 / 불일치 목록 출력
  3. 일치 span = 자동 채택. 불일치 = disagreements.jsonl (2인이 조정)
  4. (조정 후) --adjudicated resolved.jsonl 주면 최종 gold 병합

산식: span = (start, end, type). A∩B = 합의, A only/B only = 불일치.
  precision/recall 은 대칭(둘 중 누구를 gold로 봐도 같은 F1). κ-유사 일치율도 보고.

⚠️ 자동화 불가 부분: 라벨 자체 + 불일치 조정은 사람. 본 도구는 집계/검출만.

사용:
  python eval_indomain/reconcile.py
  python eval_indomain/reconcile.py --a annotator_minwoo.jsonl --b annotator_yangyusang.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_VALID_TYPES = {"NAME", "ADDRESS", "ORG"}
_MARKUP = re.compile(r"\{\{(\w+)\|(.*?)\}\}")


def parse_markup(annotated: str) -> tuple[str, list[tuple[int, int, str]], list[str]]:
    """'{{NAME|홍길동}}님' → (clean='홍길동님', spans=[(0,3,'NAME')], warnings)."""
    clean_parts: list[str] = []
    spans: list[tuple[int, int, str]] = []
    warnings: list[str] = []
    pos = 0  # clean-text 기준 위치
    last = 0
    for m in _MARKUP.finditer(annotated):
        clean_parts.append(annotated[last:m.start()])
        pos += m.start() - last
        etype, surface = m.group(1).upper(), m.group(2)
        if etype not in _VALID_TYPES:
            warnings.append(f"미지원 타입 '{etype}' (NAME/ADDRESS/ORG만)")
        if not surface.strip():
            warnings.append("빈 span")
        spans.append((pos, pos + len(surface), etype))
        clean_parts.append(surface)
        pos += len(surface)
        last = m.end()
    clean_parts.append(annotated[last:])
    return "".join(clean_parts), spans, warnings


def _load(path: Path) -> dict[str, dict]:
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rows[r["id"]] = r
    return rows


def reconcile(a_path: Path, b_path: Path) -> dict:
    A, B = _load(a_path), _load(b_path)
    ids = sorted(set(A) & set(B))
    if not ids:
        raise SystemExit("공통 id 없음 — 두 파일이 같은 candidates 에서 나왔는지 확인")

    agree = miss_a = miss_b = 0          # span 단위
    integrity_fail: list[str] = []
    markup_warn: list[str] = []
    disagreements: list[dict] = []
    gold: list[dict] = []

    for cid in ids:
        a, b = A[cid], B[cid]
        a_clean, a_spans, a_w = parse_markup(a.get("annotation", ""))
        b_clean, b_spans, b_w = parse_markup(b.get("annotation", ""))
        ref = a.get("sentence", a_clean)
        # 원문 무결성: 마크업 제거하면 원문과 같아야 (라벨러가 본문 훼손 안 했는지)
        if a_clean != ref:
            integrity_fail.append(f"[{cid}] A 본문훼손")
        if b_clean != ref:
            integrity_fail.append(f"[{cid}] B 본문훼손")
        for w in a_w: markup_warn.append(f"[{cid}] A: {w}")
        for w in b_w: markup_warn.append(f"[{cid}] B: {w}")

        sa, sb = set(a_spans), set(b_spans)
        common = sa & sb
        agree += len(common)
        miss_b += len(sa - sb)   # A 에만 (B가 놓침)
        miss_a += len(sb - sa)   # B 에만
        # 합의 span → gold
        if common:
            gold.append({"id": cid, "sentence": ref,
                         "spans": [{"start": s, "end": e, "entity_type": t}
                                   for (s, e, t) in sorted(common)]})
        if sa != sb:
            disagreements.append({
                "id": cid, "sentence": ref,
                "a_only": sorted(sa - sb), "b_only": sorted(sb - sa),
                "agreed": sorted(common),
            })

    # span-exact F1 (대칭): A를 gold, B를 pred 로 봐도 동일
    n_a = agree + miss_b   # A의 총 span
    n_b = agree + miss_a   # B의 총 span
    precision = agree / n_b if n_b else 0.0
    recall = agree / n_a if n_a else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    pct_agree = agree / (agree + miss_a + miss_b) if (agree + miss_a + miss_b) else 0.0

    return {
        "n_docs": len(ids), "agree": agree, "a_only": miss_b, "b_only": miss_a,
        "span_f1": f1, "jaccard": pct_agree,
        "integrity_fail": integrity_fail, "markup_warn": markup_warn,
        "disagreements": disagreements, "gold": gold,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default=str(_HERE / "annotator_A.jsonl"))
    ap.add_argument("--b", default=str(_HERE / "annotator_B.jsonl"))
    ap.add_argument("--out-gold", default=str(_HERE / "eval_indomain_gold.jsonl"))
    ap.add_argument("--out-disagree", default=str(_HERE / "disagreements.jsonl"))
    args = ap.parse_args()

    r = reconcile(Path(args.a), Path(args.b))

    print("=== 2인 라벨 조정 (span-exact) ===")
    print(f"  문서: {r['n_docs']}   합의 span: {r['agree']}   A만: {r['a_only']}   B만: {r['b_only']}")
    print(f"  ⭐ 라벨러 간 일치도 (span-exact F1): {r['span_f1']:.3f}")
    print(f"     Jaccard(합의/전체 span):          {r['jaccard']:.3f}")
    if r["integrity_fail"]:
        print(f"  ⚠️ 본문 훼손 {len(r['integrity_fail'])}건 (마크업 외 글자 수정 금지):")
        for x in r["integrity_fail"][:8]:
            print(f"     {x}")
    if r["markup_warn"]:
        print(f"  ⚠️ 마크업 경고 {len(r['markup_warn'])}건:")
        for x in r["markup_warn"][:8]:
            print(f"     {x}")

    Path(args.out_disagree).write_text(
        "\n".join(json.dumps(d, ensure_ascii=False) for d in r["disagreements"]), encoding="utf-8")
    Path(args.out_gold).write_text(
        "\n".join(json.dumps(g, ensure_ascii=False) for g in r["gold"]), encoding="utf-8")
    print(f"\n  합의 gold(자동채택):  {len(r['gold'])} 문서 → {Path(args.out_gold).name}")
    print(f"  불일치(조정 필요):    {len(r['disagreements'])} 문서 → {Path(args.out_disagree).name}")
    if r["span_f1"] < 0.7 and r["agree"] + r["a_only"] + r["b_only"] > 0:
        print(f"\n  ⚠️ 일치도 낮음(<0.70) — 라벨 가이드 합의 부족. 불일치 검토 후 가이드 보강 권장.")


if __name__ == "__main__":
    main()
