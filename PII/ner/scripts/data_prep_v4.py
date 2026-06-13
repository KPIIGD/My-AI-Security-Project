"""
v4 데이터 준비 — task #2 진단 반영.

v3 진단 (KLUE val per-entity):
  NAME    F1 0.853 (강)
  ADDRESS F1 0.692 (중간)
  ORG     F1 0.635 (약점)
→ v4 우선 = ORG 보강 + 외부 transfer 끌어올리기

v2 실패 트랩 회피:
  - char-level 데이터만 사용 (Naver 어절→char 노이즈 X)
  - 변수 한 번에 하나만 (v4-pre = corpus4everyone 추가만, 다른 setup 동일)
  - train ∩ KLUE val 사전 dedup (평가 누설 X)

변경점 (v3 → v4):
  1. ORG pool 24 → org_krx.txt 2,764개 (+ 기존 24 화이트리스트)
  2. corpus4everyone-korean-NER train 117k 통합 (char-level, PS/OG/LC 매핑)
  3. train ∩ KLUE val char-level sentence hash dedup
  4. Faker baseline 10k → 5k (corpus4everyone 추가로 합성 비중 축소)

총 train pool (예상):
  KLUE 21k + corpus4everyone subset (dedup 후) + Faker 5k + composite 2k + hard_neg 1k
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# v3 스키마 그대로
PII_LABELS = ["O", "B-NAME", "I-NAME", "B-ADDRESS", "I-ADDRESS", "B-ORG", "I-ORG"]
LABEL2ID = {l: i for i, l in enumerate(PII_LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

KLUE_TO_PII = {
    "B-PS": "B-NAME", "I-PS": "I-NAME",
    "B-LC": "B-ADDRESS", "I-LC": "I-ADDRESS",
    "B-OG": "B-ORG", "I-OG": "I-ORG",
}

# corpus4everyone-korean-NER 라벨 (30 = O, 0/1=PS, 8/9=OG, 10/11=LC)
CORPUS4EV_TO_PII = {
    0: "B-NAME", 1: "I-NAME",
    8: "B-ORG", 9: "I-ORG",
    10: "B-ADDRESS", 11: "I-ADDRESS",
    # 그 외 13개 entity (FD/TR/AF/CV/DT/TI/QT/EV/AM/PT/MT/TM) → O (우리 스키마 밖)
}
CORPUS4EV_PATH = ROOT / "data" / "external" / "huggingface" / \
    "datasciathlete__corpus4everyone-korean-NER" / "data"


def _sentence_hash(chars: list[str]) -> str:
    """char-level token list → 정규화된 sentence hash (whitespace 흡수)."""
    s = "".join(chars).strip()
    s = "".join(s.split())  # 모든 whitespace 제거 (변형 흡수)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


# ─────────────────────────────────────────────────────────
# KLUE-NER 로더 (data_prep_v3.py 동일)
# ─────────────────────────────────────────────────────────
def load_klue_split(split: str = "train") -> list[dict]:
    """기존 pii_ner_v3.json 에서 캐시 로드 (HF Hub offline).

    v3 json 의 train/val/test 는 KLUE+Faker 섞은 8:1:1 split. 원래 KLUE train 21k 전체를
    되찾으려면 세 split 다 합쳐서 source="klue_ner" 추출.
    """
    cached = json.load((ROOT / "data" / "pii_ner_v3.json").open(encoding="utf-8"))
    if split == "train":
        all_v3 = cached["train"] + cached["val"] + cached["test"]
        src = [s for s in all_v3 if s.get("source") == "klue_ner"]
    elif split == "validation":
        src = cached["klue_test"]
    else:
        raise ValueError(split)
    return src


# ─────────────────────────────────────────────────────────
# corpus4everyone-korean-NER 로더 (신규)
# ─────────────────────────────────────────────────────────
# R1-i03 fix: AF/EV/CV 가 PS/OG/LC 와 인접하면 false negative 학습 위험
# 옵션 (--exclude-confusable): AF(6,7) / EV(20,21) / CV(12,13) 가 있는 sentence 자체 제외
CORPUS4EV_CONFUSABLE_TAGS = {6, 7, 20, 21, 12, 13}  # AF, EV, CV


def load_corpus4everyone(split: str = "train", limit: int = 0,
                         exclude_confusable: bool = False) -> list[dict]:
    """parquet 직접 로드. PS/OG/LC 만 우리 스키마 매핑, 나머지는 O.

    R1-i03 fix: exclude_confusable=True 시 AF/EV/CV 라벨 포함 sentence 제외 (false negative 차단).
    R1-i07 fix: corpus 자체 sentence hash dedup 추가.
    """
    import pyarrow.parquet as pq
    fname = f"{split}-00000-of-00001.parquet"
    fpath = CORPUS4EV_PATH / fname
    if not fpath.exists():
        raise FileNotFoundError(f"corpus4everyone 파일 없음: {fpath}")
    print(f"  Loading corpus4everyone {split} from {fpath}...")
    table = pq.read_table(str(fpath))
    rows = table.to_pylist()
    print(f"    raw rows: {len(rows)}")
    if limit > 0:
        rows = rows[:limit]
        print(f"    [LIMIT] {limit}")

    samples = []
    seen_hashes = set()  # R1-i07 자체 dedup
    n_confusable_dropped = 0
    n_self_dup = 0
    for r in rows:
        tokens = list(r["tokens"])
        tag_ids = r["ner_tags"]
        if not tokens or not tag_ids:
            continue
        if len(tokens) != len(tag_ids):
            continue
        tag_id_set = set(int(t) for t in tag_ids)
        # R1-i03: confusable 라벨 있으면 sentence 제외
        if exclude_confusable and tag_id_set & CORPUS4EV_CONFUSABLE_TAGS:
            n_confusable_dropped += 1
            continue
        # R1-i07: 자체 dedup
        h = _sentence_hash(tokens)
        if h in seen_hashes:
            n_self_dup += 1
            continue
        seen_hashes.add(h)

        label_names = [CORPUS4EV_TO_PII.get(int(t), "O") for t in tag_ids]
        samples.append({
            "tokens": tokens,
            "labels": [LABEL2ID[l] for l in label_names],
            "label_names": label_names,
            "sentence": "".join(tokens),
            "source": "corpus4everyone",
        })
    print(f"    mapped samples: {len(samples)}")
    if exclude_confusable:
        print(f"    confusable (AF/EV/CV) dropped: {n_confusable_dropped}")
    if n_self_dup:
        print(f"    self-dedup removed: {n_self_dup}")
    return samples


# ─────────────────────────────────────────────────────────
# ORG pool 확장 (org_krx.txt 2,764개 + 기존 24개 화이트리스트)
# ─────────────────────────────────────────────────────────
def load_org_pool_v4() -> list[str]:
    """KRX 상장사 2,764 + v3 화이트리스트 (대학·병원·금융·공공)."""
    krx_path = ROOT / "data" / "external" / "public" / "org_krx.txt"
    krx = [l.strip() for l in krx_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"  KRX 상장사: {len(krx)}")

    # v3 화이트리스트 (대학·병원·공공·IT/유통 미상장 — KRX 에 없는 카테고리)
    # R1-i01 fix: v3 24개 중 5개 (포스코/네이버/쿠팡/네이버클라우드/토스) KRX 누락 추가
    v3_extras = [
        # v3 IT/유통/철강 (KRX 누락 — R1-i01 fix)
        "포스코", "네이버", "쿠팡", "네이버클라우드", "토스",
        # 대학교
        "서울대학교", "연세대학교", "고려대학교", "한양대학교", "성균관대학교",
        "포항공과대학교", "카이스트", "KAIST", "유니스트", "UNIST",
        # 병원
        "세브란스병원", "삼성서울병원", "아산병원", "서울대병원", "서울대학교병원",
        # 공공
        "국세청", "관세청", "검찰청", "경찰청", "건강보험공단", "국민연금공단",
        # 금융
        "신한은행", "국민은행", "우리은행", "하나은행",
    ]
    merged = list(dict.fromkeys(krx + v3_extras))  # 순서 보존 중복 제거
    print(f"  v3 extras 추가 후: {len(merged)} (KRX {len(krx)} + extras {len(v3_extras)} - 중복)")
    return merged


# ─────────────────────────────────────────────────────────
# 합성 (data_prep_v3.py 그대로, org_pool 만 v4 풀로 교체)
# ─────────────────────────────────────────────────────────
BASIC_TEMPLATES = [
    "안녕하세요, 저는 {name}입니다.",
    "{name}님께 연락드립니다.",
    "{name}이 등록하셨습니다.",
    "고객명: {name}, 가입일자는 어제입니다.",
    "담당자 {name} 과장님께 문의해 주세요.",
    "{name}씨가 방문 예정입니다.",
    "주소는 {address} 입니다.",
    "배송지: {address}",
    "{address}로 우편물을 보내주세요.",
    "{address}에 거주 중입니다.",
    "{name}님은 {org} 소속입니다.",
    "{org}에 입사했습니다.",
    "{org}의 담당자는 {name}입니다.",
    "{name}({age}세)는 {address}에 거주하며 {org}에서 근무합니다.",
    "환자 {name}님 ({org} 소속)이 진료 받으셨습니다.",
    "{address}에 위치한 {org}로 방문하시면 됩니다.",
]

COMPOSITE_TEMPLATES = [
    "저는 {name}이고 {address}에 거주합니다.",
    "저는 {name}이며 {org} 소속입니다.",
    "{name}이고 {org} 임원입니다.",
    "안녕하세요, 저는 {name}입니다. {address}에 살고 {org}에 다녀요.",
    "{name}과 {name2}가 {address}에서 만났습니다.",
    "{name}와 {org} 대표가 회의했습니다.",
    "{name}이랑 {org}에 다닙니다.",
    "환자 {name}({age}세)는 {address}에 거주하며 {org}에서 근무합니다.",
    "{name}님은 {org}에서 일하고 {address}에 사십니다.",
    "고객 {name}이 {org}에 가입했으며 {address}로 청구서를 받습니다.",
    "발표자 {name}, 소속 {org}, 주소 {address}.",
    "{name}/{name2} 공동저자, 소속 {org}.",
    "수신인: {name} (소속: {org}), 주소: {address}",
]

HARD_NEGATIVE_TEMPLATES = [
    "오늘 {weather}이 {adj}네요.",
    "{abstract}은 중요한 가치입니다.",
    "고객센터 대표번호는 1588-{4d}입니다.",
    "예시 전화번호는 010-0000-0000입니다.",
    "{weather}처럼 맑은 날이 좋아요.",
    "{food}을 좋아하시나요?",
    "오늘 메뉴는 {food}입니다.",
]

WEATHER = ["하늘", "별", "햇빛", "구름", "바다", "산", "강", "노을", "달빛"]
ABSTRACT = ["사랑", "우정", "평화", "자유", "행복", "지혜", "용기", "정의", "신뢰"]
FOOD = ["김치", "비빔밥", "떡볶이", "라면", "치킨", "삼겹살", "된장찌개"]


def label_substring(sentence, entity_text, entity_type, char_labels):
    if not entity_text:
        return
    idx = sentence.find(entity_text)
    if idx < 0:
        return
    end = idx + len(entity_text)
    if char_labels[idx] != "O":
        return
    char_labels[idx] = f"B-{entity_type}"
    for j in range(idx + 1, end):
        if j < len(char_labels) and char_labels[j] == "O":
            char_labels[j] = f"I-{entity_type}"


def gen_faker(count, rng, addr_pairs, org_pool, templates, source_name):
    from faker import Faker
    sys.path.insert(0, str(ROOT / "scripts"))
    from korean_address import random_address
    fake = Faker("ko_KR")
    Faker.seed(rng.randint(0, 99999))

    samples = []
    for _ in range(count):
        tmpl = rng.choice(templates)
        name = fake.name()
        name2 = fake.name()
        while name2 == name:
            name2 = fake.name()
        address = random_address(rng, addr_pairs)
        org = rng.choice(org_pool)
        age = rng.randint(20, 70)
        try:
            sentence = tmpl.format(name=name, name2=name2, address=address, org=org, age=age)
        except KeyError:
            continue
        chars = list(sentence)
        labels = ["O"] * len(chars)
        ents = sorted(
            [(name, "NAME"), (name2, "NAME"), (address, "ADDRESS"), (org, "ORG")],
            key=lambda t: -len(t[0])
        )
        for ent_text, etype in ents:
            label_substring(sentence, ent_text, etype, labels)
        samples.append({
            "tokens": chars,
            "labels": [LABEL2ID[l] for l in labels],
            "label_names": labels,
            "sentence": sentence,
            "source": source_name,
        })
    return samples


def gen_hard_neg(count, rng):
    samples = []
    for _ in range(count):
        tmpl = rng.choice(HARD_NEGATIVE_TEMPLATES)
        sentence = tmpl.format(
            weather=rng.choice(WEATHER),
            abstract=rng.choice(ABSTRACT),
            food=rng.choice(FOOD),
            adj=rng.choice(["맑네요", "좋네요", "예쁘네요", "선선하네요"]),
            **{"4d": f"{rng.randint(0,9999):04d}"},
        )
        chars = list(sentence)
        labels = ["O"] * len(chars)
        samples.append({
            "tokens": chars,
            "labels": [LABEL2ID[l] for l in labels],
            "label_names": labels,
            "sentence": sentence,
            "source": "hard_negative_v4",
        })
    return samples


# ─────────────────────────────────────────────────────────
# Stats
# ─────────────────────────────────────────────────────────
def stats(samples):
    c = Counter()
    for s in samples:
        for lab in s["label_names"]:
            if lab.startswith("B-"):
                c[lab[2:]] += 1
    return dict(c)


def split_8_1_1(samples, seed=42):
    rng = random.Random(seed)
    idx = list(range(len(samples)))
    rng.shuffle(idx)
    n = len(idx)
    return ([samples[i] for i in idx[:int(n*0.8)]],
            [samples[i] for i in idx[int(n*0.8):int(n*0.9)]],
            [samples[i] for i in idx[int(n*0.9):]])


# ─────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="../data/pii_ner_v4.json")
    p.add_argument("--faker-baseline", type=int, default=5000,
                   help="v3 10k → v4 5k (corpus4everyone 추가로 합성 비중 축소)")
    p.add_argument("--composite", type=int, default=2000)
    p.add_argument("--hard-neg", type=int, default=1000)
    p.add_argument("--corpus4ev-limit", type=int, default=30000,
                   help="corpus4everyone 샘플 제한. R2-i03 fix default 30000 "
                        "(corpus 약 53pct vs KLUE 37pct vs Faker 10pct, v2 81pct 트랩 회피). "
                        "0 = 전체 117k, ablation 시 명시 사용.")
    p.add_argument("--exclude-confusable", action="store_true",
                   help="R2-i02 fix: corpus4everyone AF/EV/CV (제품/이벤트/직책) 라벨 "
                        "포함 sentence 제외. ORG/NAME 과 confusable 학습 차단. "
                        "trade-off: NAME label 추가 희석.")
    args = p.parse_args()

    print("=" * 70)
    print("  PII NER v4 dataset")
    print("=" * 70)
    print("  Key changes from v3:")
    print(f"    + ORG pool 24 → ~2,795 (org_krx.txt 2,765 + v3 extras 30)")
    print("    + corpus4everyone-korean-NER (char-level, PS/OG/LC 매핑)")
    print(f"    + corpus4ev limit: {args.corpus4ev_limit} (0=전체 117k)")
    print(f"    + exclude_confusable (AF/EV/CV): {args.exclude_confusable}")
    print("    + train ∩ KLUE val sentence hash dedup + corpus 자체 dedup")
    print("    - Faker baseline 10k → 5k (비중 균형)")
    print()

    rng = random.Random(42)

    # 1. KLUE
    klue_train = load_klue_split("train")
    klue_val = load_klue_split("validation")
    print(f"  KLUE train: {len(klue_train)} | val: {len(klue_val)}")

    # 2. corpus4everyone (R2-i02 fix: exclude_confusable 옵션 전달)
    corpus_train = load_corpus4everyone(
        "train",
        limit=args.corpus4ev_limit,
        exclude_confusable=args.exclude_confusable,
    )

    # 3. dedup: train ∩ klue_val (평가 누설 차단)
    klue_val_hashes = {_sentence_hash(s["tokens"]) for s in klue_val}
    before = len(corpus_train) + len(klue_train)
    corpus_train = [s for s in corpus_train if _sentence_hash(s["tokens"]) not in klue_val_hashes]
    klue_train = [s for s in klue_train if _sentence_hash(s["tokens"]) not in klue_val_hashes]
    after = len(corpus_train) + len(klue_train)
    print(f"  Dedup train ∩ klue_val: {before} → {after} (removed {before - after})")

    # 4. KLUE 자기 중복 (KLUE train ∩ corpus4everyone train)
    klue_train_hashes = {_sentence_hash(s["tokens"]) for s in klue_train}
    before = len(corpus_train)
    corpus_train = [s for s in corpus_train if _sentence_hash(s["tokens"]) not in klue_train_hashes]
    print(f"  Dedup corpus4ev ∩ klue_train: {before} → {len(corpus_train)} (removed {before - len(corpus_train)})")

    # 5. ORG pool 확장 + 주소 페어
    print()
    print("  Loading ORG pool v4...")
    org_pool = load_org_pool_v4()

    sys.path.insert(0, str(ROOT / "scripts"))
    from korean_address import load_admin_pairs
    addr_pairs = load_admin_pairs()

    # 6. Faker 합성
    print()
    print(f"  Generating Faker baseline ({args.faker_baseline})...")
    faker_base = gen_faker(args.faker_baseline, rng, addr_pairs, org_pool, BASIC_TEMPLATES, "faker_baseline_v4")
    print(f"    {len(faker_base)}")

    print(f"  Generating composite ({args.composite})...")
    composite = gen_faker(args.composite, rng, addr_pairs, org_pool, COMPOSITE_TEMPLATES, "faker_composite_v4")
    print(f"    {len(composite)}")

    print(f"  Generating hard negatives ({args.hard_neg})...")
    hard_neg = gen_hard_neg(args.hard_neg, rng)
    print(f"    {len(hard_neg)}")

    # 7. 통합 + split
    all_train = klue_train + corpus_train + faker_base + composite + hard_neg
    random.Random(42).shuffle(all_train)
    train, val, test = split_8_1_1(all_train)

    print()
    print("=" * 70)
    print("  Stats")
    print("=" * 70)
    print(f"  Total pool: {len(all_train):>7,}")
    print(f"    klue_train             {len(klue_train):>7,} ({len(klue_train)*100/len(all_train):.1f}%)")
    print(f"    corpus4everyone        {len(corpus_train):>7,} ({len(corpus_train)*100/len(all_train):.1f}%)")
    print(f"    faker_baseline_v4      {len(faker_base):>7,} ({len(faker_base)*100/len(all_train):.1f}%)")
    print(f"    faker_composite_v4     {len(composite):>7,} ({len(composite)*100/len(all_train):.1f}%)")
    print(f"    hard_negative_v4       {len(hard_neg):>7,} ({len(hard_neg)*100/len(all_train):.1f}%)")
    print()
    print(f"  Train: {len(train):>7,} | entities: {stats(train)}")
    print(f"  Val:   {len(val):>7,}")
    print(f"  Test:  {len(test):>7,}")
    print(f"  KLUE val (external): {len(klue_val):>7,}")

    data = {
        "label2id": LABEL2ID,
        "id2label": ID2LABEL,
        "train": train,
        "val": val,
        "test": test,
        "klue_test": klue_val,
        "meta": {
            "version": "v4",
            "klue": len(klue_train),
            "corpus4everyone": len(corpus_train),
            "faker_baseline": len(faker_base),
            "composite": len(composite),
            "hard_negative": len(hard_neg),
            "org_pool_size": len(org_pool),
            "dedup_applied": True,
        },
    }
    out = Path(args.output) if args.output.startswith("/") else ROOT / args.output.lstrip("./")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    size_mb = out.stat().st_size / 1024 / 1024
    print(f"\n[Saved] {out.resolve()} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
