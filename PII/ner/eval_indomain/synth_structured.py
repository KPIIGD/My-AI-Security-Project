"""구조형 PII 합성기 — 평가셋용 (#2 합성 + #3 in-domain 평가).

여권/면허/법인/차량/카드/계좌/RRN 을 **정확한 형식 + (가능하면) 유효 체크섬**으로
생성해 자연스러운 챗 문장에 박는다. 합성이므로 span/type 이 자동으로 정확 → 사람 라벨
불필요(구조형 PII 트랙). 출력은 v0.2 regex detector 평가 + NER 평가 보강에 쓴다.

v0.2 detector 호환:
  - 여권/면허 detector 는 라벨 context("여권번호:" 등) 필수 → with_label 템플릿이 그걸 만족.
  - 법인 detector 는 알려진 등기소 prefix(110111 등)만 매칭 → 동일 prefix 사용.
  - 일부는 label 없는 음성(negative) 케이스로 만들어 precision(오탐 안 함) 평가.

⚠️ 전부 합성. 실존 인물/기관과 무관. 계좌/카드는 enumeration 방지 위해 형식만 모사.

사용:
  python eval_indomain/synth_structured.py --n 300 --out eval_indomain/structured_eval.jsonl
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

# ── 형식/체크섬 생성기 ─────────────────────────────────────────────

_RRN_WEIGHTS = (2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5)
_CORP_WEIGHTS = (1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2)
_CORP_PREFIXES = ("110111", "110114", "110115", "110121", "134511")  # v0.2 detector 와 일치
_PASSPORT_LETTERS = "MSRODG"
_DL_REGIONS = [f"{c:02d}" for c in range(11, 40)]
_PLATE_HANGUL = "가나다라마거너더러머버서어저고노도로모보소오조구누두루무부수우주바사아자하허호"


def _rrn(rng: random.Random) -> str:
    yy = rng.randint(0, 99); mm = rng.randint(1, 12); dd = rng.randint(1, 28)
    g = rng.choice("1234")  # 1900s/2000s 내국인
    body = f"{yy:02d}{mm:02d}{dd:02d}{g}{rng.randint(0, 999999):06d}"
    s = sum(int(d) * w for d, w in zip(body[:12], _RRN_WEIGHTS))
    check = (11 - (s % 11)) % 10
    return f"{body[:6]}-{body[6:]}{check}"


def _card(rng: random.Random) -> str:
    """16자리 Luhn 유효 카드번호 (형식만)."""
    digits = [rng.randint(0, 9) for _ in range(15)]
    # Luhn check digit
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 0:  # 곧 check 앞에서 두 배 위치
            d *= 2
            if d > 9: d -= 9
        total += d
    check = (10 - (total % 10)) % 10
    digits.append(check)
    s = "".join(map(str, digits))
    return f"{s[:4]}-{s[4:8]}-{s[8:12]}-{s[12:]}"


def _account(rng: random.Random) -> str:
    return f"{rng.randint(100, 999)}-{rng.randint(10, 99)}-{rng.randint(100000, 999999)}"


def _passport(rng: random.Random) -> str:
    return f"{rng.choice(_PASSPORT_LETTERS)}{rng.randint(0, 99999999):08d}"


def _driver_license(rng: random.Random) -> str:
    region = rng.choice(_DL_REGIONS)
    return f"{region}-{rng.randint(0, 99):02d}-{rng.randint(0, 999999):06d}-{rng.randint(0, 99):02d}"


def _corporate(rng: random.Random) -> str:
    prefix = rng.choice(_CORP_PREFIXES)
    serial = f"{rng.randint(0, 999999):06d}"
    body = prefix + serial
    s = sum(int(d) * w for d, w in zip(body, _CORP_WEIGHTS))
    check = (10 - (s % 10)) % 10
    return f"{prefix}-{serial}{check}"


def _vehicle(rng: random.Random) -> str:
    head = rng.choice([2, 3])
    h = "".join(str(rng.randint(0, 9)) for _ in range(head))
    return f"{h}{rng.choice(_PLATE_HANGUL)}{rng.randint(0, 9999):04d}"


# ── 챗 템플릿: {label} 가 있으면 라벨 context(v0.2 detector 발화), {bare}=음성 ──
# 각 항목: (entity_type, generator, [라벨문맥 템플릿...], [무라벨 템플릿...])
_SPECS = [
    ("PASSPORT", _passport,
     ["여권번호 {v} 인데 갱신 가능할까요?", "제 여권번호는 {v} 입니다. 확인 부탁드려요.",
      "passport no: {v} 로 예약했어요."],
     ["출장 가는데 {v} 어쩌고 적어놨더라.", "메모에 {v} 라고만 써있어요."]),
    ("DRIVER_LICENSE", _driver_license,
     ["운전면허번호 {v} 로 렌트 예약했습니다.", "면허번호는 {v} 예요.",
      "driver license {v} 등록해주세요."],
     ["코드 {v} 가 뭔지 모르겠어요.", "그냥 {v} 라고 적혀있던데요."]),
    ("CORPORATE_REG_NO", _corporate,
     ["법인등록번호 {v} 로 사업자 등록했어요.", "회사 법인번호는 {v} 입니다."],
     ["문서에 {v} 숫자가 있던데 뭐죠?"]),
    ("VEHICLE_REG_NO", _vehicle,
     ["차량번호 {v} 주차 위반 조회해주세요.", "제 차 번호판 {v} 입니다."],
     ["{v} 지나갔어요.", "{v} 차 봤어요."]),
    ("CREDIT_CARD", _card,
     ["카드번호 {v} 로 결제했어요.", "신용카드 {v} 승인 확인 부탁해요."],
     ["{v} 영수증 번호 같던데요."]),
    ("BANK_ACCOUNT", _account,
     ["계좌번호 {v} 로 입금해주세요.", "제 계좌는 신한 {v} 입니다."],
     ["주문번호 {v} 조회요.", "예약번호 {v} 확인해주세요."]),
    ("RRN", _rrn,
     ["주민등록번호 {v} 로 본인확인했어요.", "주민번호는 {v} 예요."],
     ["{v} 비슷한 숫자만 기억나요."]),
]


def generate(n: int, *, neg_ratio: float = 0.25, seed: int = 20260604) -> list[dict]:
    """구조형 PII 합성 example n 건. neg_ratio 비율은 라벨문맥 없는 음성(precision 평가용).

    return: [{sentence, spans:[{start,end,entity_type,value}], has_label_context, source_type}]
    """
    rng = random.Random(seed)
    out: list[dict] = []
    for _ in range(n):
        etype, gen, pos_tpls, neg_tpls = rng.choice(_SPECS)
        is_neg = rng.random() < neg_ratio and neg_tpls
        tpl = rng.choice(neg_tpls if is_neg else pos_tpls)
        value = gen(rng)
        sentence = tpl.format(v=value)
        start = sentence.index(value)
        out.append({
            "sentence": sentence,
            "spans": [{"start": start, "end": start + len(value),
                       "entity_type": etype, "value": value}],
            "has_label_context": not is_neg,
            "source_type": "synth_structured",
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--neg-ratio", type=float, default=0.25)
    ap.add_argument("--seed", type=int, default=20260604)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "structured_eval.jsonl"))
    args = ap.parse_args()

    rows = generate(args.n, neg_ratio=args.neg_ratio, seed=args.seed)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    pos = sum(1 for r in rows if r["has_label_context"])
    by_type: dict[str, int] = {}
    for r in rows:
        by_type[r["spans"][0]["entity_type"]] = by_type.get(r["spans"][0]["entity_type"], 0) + 1
    print(f"=== 구조형 PII 합성 {len(rows)} 건 → {out_path} ===")
    print(f"  라벨문맥 있음(positive): {pos}  /  음성(precision용): {len(rows) - pos}")
    print(f"  타입별: {by_type}")


if __name__ == "__main__":
    main()
