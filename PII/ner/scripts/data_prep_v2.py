"""
W2 v2 데이터 준비 — 더 많은 실데이터 통합.

소스:
  1. KLUE-NER train 21,008  (CC-BY-SA, 기존)
  2. Naver NER 2018 90,001  (Naver 공개 데이터, challenge용)
  3. WikiAnn ko 20,000 + val 10,000  (CC-BY-SA, Wikipedia 기반)
  4. Faker-ko 5,000 (기존 합성 축소)
  5. Faker conjunctive composite 2,000 (신규 — v1 한계 보완)

총: ~138k sentences (v1의 31k 대비 4.4배)

평가용 별도 외부 셋:
  - KLUE-NER validation 5,000
  - WikiAnn ko test 10,000

출력 라벨: O, B/I-NAME, B/I-ADDRESS, B/I-ORG (v1 동일)

사용:
  python data_prep_v2.py --output ../data/pii_ner_v2.json
"""
from __future__ import annotations
import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path

from datasets import load_dataset

PII_LABELS = ["O", "B-NAME", "I-NAME", "B-ADDRESS", "I-ADDRESS", "B-ORG", "I-ORG"]
LABEL2ID = {l: i for i, l in enumerate(PII_LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}


# ─────────────────────────────────────────────────────────
# 1. KLUE-NER (기존)
# ─────────────────────────────────────────────────────────
KLUE_TO_PII = {
    "B-PS": "B-NAME", "I-PS": "I-NAME",
    "B-LC": "B-ADDRESS", "I-LC": "I-ADDRESS",
    "B-OG": "B-ORG", "I-OG": "I-ORG",
}


def load_klue_split(split: str = "train") -> list[dict]:
    print(f"  Loading KLUE-NER {split}...")
    ds = load_dataset("klue", "ner", split=split)
    label_names = ds.features["ner_tags"].feature.names
    samples = []
    for s in ds:
        chars = s["tokens"]
        klue_tags = [label_names[t] for t in s["ner_tags"]]
        pii_tags = [KLUE_TO_PII.get(t, "O") for t in klue_tags]
        samples.append({
            "tokens": chars,
            "labels": [LABEL2ID[t] for t in pii_tags],
            "label_names": pii_tags,
            "sentence": "".join(chars),
            "source": "klue_ner",
        })
    print(f"    {len(samples)} samples")
    return samples


# ─────────────────────────────────────────────────────────
# 2. Naver NER 2018
# ─────────────────────────────────────────────────────────
NAVER_TO_PII = {
    "PER": "NAME",
    "LOC": "ADDRESS",
    "ORG": "ORG",
    # 나머지(DAT/NUM/TIM/CVL/FLD/AFW/PNT/ANM/PLT/MAT/TRM/EVT) → O
}


def parse_naver_ner(file_path: Path) -> list[dict]:
    """Naver NER train_data 파싱.

    Format:
        idx<TAB>word<TAB>label_TYPE_B|TYPE_I|-
        (빈 줄 = 문장 구분)

    어절 단위 라벨이라 char 시퀀스로 풀어야 함. 어절 첫 글자는 B-, 나머지는 I-,
    어절 사이엔 공백 (label O).
    """
    print(f"  Loading Naver NER from {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    sentences = content.strip().split("\n\n")
    samples = []
    skipped = 0
    for sent in sentences:
        lines = sent.strip().split("\n")
        if not lines:
            continue
        eojeols = []  # list of (word, label_str)
        valid = True
        for line in lines:
            parts = line.strip().split("\t")
            if len(parts) != 3:
                valid = False
                break
            idx, word, label = parts
            eojeols.append((word, label))
        if not valid or not eojeols:
            skipped += 1
            continue

        # char-level expansion
        chars = []
        label_names = []
        for i, (word, label) in enumerate(eojeols):
            if i > 0:
                chars.append(" ")
                label_names.append("O")
            for j, ch in enumerate(word):
                chars.append(ch)
                if label == "-":
                    label_names.append("O")
                else:
                    # label format: TYPE_B or TYPE_I
                    if "_" in label:
                        type_, bi = label.rsplit("_", 1)
                        pii_type = NAVER_TO_PII.get(type_)
                        if pii_type is None:
                            label_names.append("O")
                        else:
                            if bi == "B":
                                label_names.append(f"B-{pii_type}" if j == 0 else f"I-{pii_type}")
                            else:  # I
                                label_names.append(f"I-{pii_type}")
                    else:
                        label_names.append("O")

        samples.append({
            "tokens": chars,
            "labels": [LABEL2ID[l] for l in label_names],
            "label_names": label_names,
            "sentence": "".join(chars),
            "source": "naver_ner_2018",
        })

    print(f"    {len(samples)} samples (skipped {skipped} malformed)")
    return samples


# ─────────────────────────────────────────────────────────
# 3. WikiAnn ko
# ─────────────────────────────────────────────────────────
WIKIANN_LABEL_NAMES = ["O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-LOC", "I-LOC"]
WIKIANN_TO_PII = {
    "O": "O",
    "B-PER": "B-NAME", "I-PER": "I-NAME",
    "B-ORG": "B-ORG", "I-ORG": "I-ORG",
    "B-LOC": "B-ADDRESS", "I-LOC": "I-ADDRESS",
}


def load_wikiann_split(split: str = "train") -> list[dict]:
    """WikiAnn ko split — token-level (word 기준)."""
    print(f"  Loading WikiAnn ko {split}...")
    ds = load_dataset("wikiann", "ko", split=split)
    samples = []
    for s in ds:
        words = s["tokens"]
        word_tags = [WIKIANN_LABEL_NAMES[t] for t in s["ner_tags"]]

        # char-level expansion (단어 사이 공백)
        chars = []
        label_names = []
        for i, (word, tag) in enumerate(zip(words, word_tags)):
            if i > 0:
                chars.append(" ")
                label_names.append("O")
            pii_tag = WIKIANN_TO_PII[tag]
            for j, ch in enumerate(word):
                chars.append(ch)
                if pii_tag == "O":
                    label_names.append("O")
                elif pii_tag.startswith("B-"):
                    label_names.append(pii_tag if j == 0 else f"I-{pii_tag[2:]}")
                else:  # I-
                    label_names.append(pii_tag)

        samples.append({
            "tokens": chars,
            "labels": [LABEL2ID[l] for l in label_names],
            "label_names": label_names,
            "sentence": "".join(chars),
            "source": f"wikiann_ko_{split}",
        })
    print(f"    {len(samples)} samples")
    return samples


# ─────────────────────────────────────────────────────────
# 4. Faker baseline (축소 5k)
# ─────────────────────────────────────────────────────────
BASIC_TEMPLATES = [
    "안녕하세요, 저는 {name}입니다.",
    "{name}님께 연락드립니다.",
    "고객명: {name}, 가입일자는 어제입니다.",
    "담당자 {name} 과장님께 문의해 주세요.",
    "{name}씨가 방문 예정입니다.",
    "주소는 {address} 입니다.",
    "배송지: {address}",
    "{address}로 우편물을 보내주세요.",
    "{address}에 거주 중입니다.",
    "{org}에 입사했습니다.",
    "이번 회의는 {org} 본사에서 진행됩니다.",
]

# ─────────────────────────────────────────────────────────
# 5. v2 신규: Conjunctive composite + hard negatives
# ─────────────────────────────────────────────────────────
COMPOSITE_TEMPLATES = [
    # NAME 이고/이며 + ADDR/ORG
    "저는 {name}이고 {address}에 거주합니다.",
    "저는 {name}이며 {org} 소속입니다.",
    "담당자는 {name}이고 {org}에서 일합니다.",
    "{name}이고 {org} 임원입니다.",
    # NAME 과/와 + NAME/ORG
    "{name}과 {name2}가 {address}에서 만났습니다.",
    "{name}와 {org} 대표가 회의했습니다.",
    # NAME 하고/이랑
    "{name}하고 {name2}이 같이 왔어요.",
    "{name}이랑 {org}에 다닙니다.",
    # ADDR 에서/로/까지 + NAME
    "{name}가 {address}에서 일합니다.",
    "{name}이 {address}로 이사갔습니다.",
    # 복합
    "환자 {name}({age}세)는 {address}에 거주하며 {org}에서 근무합니다.",
    "{name}님은 {org}에서 일하고 {address}에 사십니다.",
    "고객 {name}이 {org}에 가입했으며 {address}로 청구서를 받습니다.",
    # 라벨 인접
    "{name}/{name2} 합동공연이 {address}에서 열렸다.",
    "발표자 {name}, 소속 {org}, 주소 {address}.",
]

HARD_NEGATIVE_TEMPLATES = [
    "오늘 {weather}이 {adj}네요.",
    "{abstract}은 중요한 가치입니다.",
    "{abstract}이 모두에게 필요합니다.",
    "고객센터 대표번호는 1588-{4d}입니다.",
    "예시 전화번호는 010-0000-0000입니다.",
    "{weather}처럼 맑은 날이 좋아요.",
    "{abstract}이라는 단어는 자주 쓰입니다.",
    "{food}을 좋아하시나요?",
]

WEATHER = ["하늘", "별", "햇빛", "구름", "바다", "산", "강"]
ABSTRACT = ["사랑", "우정", "평화", "자유", "행복", "지혜", "용기", "정의", "신뢰"]
FOOD = ["김치", "비빔밥", "떡볶이", "라면", "치킨", "삼겹살"]


def label_substring(sentence: str, entity_text: str, entity_type: str,
                    char_labels: list[str]) -> None:
    """sentence 안의 entity_text 첫 occurrence를 BIO 라벨링 (in-place)."""
    if not entity_text:
        return
    idx = sentence.find(entity_text)
    if idx < 0:
        return
    end = idx + len(entity_text)
    # 이미 라벨된 곳은 skip
    if char_labels[idx] != "O":
        return
    char_labels[idx] = f"B-{entity_type}"
    for j in range(idx + 1, end):
        if j < len(char_labels) and char_labels[j] == "O":
            char_labels[j] = f"I-{entity_type}"


def generate_faker_baseline(count: int, rng: random.Random, addr_pairs, org_pool) -> list[dict]:
    """v1 합성 (축소판)."""
    from faker import Faker
    from korean_address import random_address

    fake = Faker("ko_KR")
    Faker.seed(rng.randint(0, 99999))

    samples = []
    for _ in range(count):
        tmpl = rng.choice(BASIC_TEMPLATES)
        name = fake.name()
        address = random_address(rng, addr_pairs)
        org = rng.choice(org_pool)
        age = rng.randint(20, 70)

        sentence = tmpl.format(name=name, address=address, org=org, age=age)
        chars = list(sentence)
        labels = ["O"] * len(chars)

        for ent, etype in [(name, "NAME"), (address, "ADDRESS"), (org, "ORG")]:
            label_substring(sentence, ent, etype, labels)

        samples.append({
            "tokens": chars,
            "labels": [LABEL2ID[l] for l in labels],
            "label_names": labels,
            "sentence": sentence,
            "source": "faker_baseline_v2",
        })
    return samples


def generate_composite(count: int, rng: random.Random, addr_pairs, org_pool) -> list[dict]:
    """v2 신규: conjunctive composite — v1 한계 보완."""
    from faker import Faker
    from korean_address import random_address

    fake = Faker("ko_KR")
    Faker.seed(rng.randint(0, 99999))

    samples = []
    for _ in range(count):
        tmpl = rng.choice(COMPOSITE_TEMPLATES)
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

        # 라벨링 우선순위: 긴 entity 먼저 (substring overlap 방지)
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
            "source": "faker_composite_v2",
        })
    return samples


def generate_hard_negatives(count: int, rng: random.Random) -> list[dict]:
    """v2 신규: hard negatives (NAME처럼 보이는 일반명사, public number 등)."""
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
        labels = ["O"] * len(chars)  # negative: 모두 O

        samples.append({
            "tokens": chars,
            "labels": [LABEL2ID[l] for l in labels],
            "label_names": labels,
            "sentence": sentence,
            "source": "hard_negative_v2",
        })
    return samples


# ─────────────────────────────────────────────────────────
# stats + split
# ─────────────────────────────────────────────────────────
def stats(samples: list[dict]) -> dict:
    counter = Counter()
    for s in samples:
        for lab in s["label_names"]:
            if lab.startswith("B-"):
                counter[lab[2:]] += 1
    return dict(counter)


def split_8_1_1(samples: list[dict], seed: int = 42):
    random.seed(seed)
    indices = list(range(len(samples)))
    random.shuffle(indices)
    n = len(indices)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)
    return ([samples[i] for i in indices[:train_end]],
            [samples[i] for i in indices[train_end:val_end]],
            [samples[i] for i in indices[val_end:]])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="../data/pii_ner_v2.json")
    p.add_argument("--naver-data", default="../data/naver_ner_train.tsv")
    p.add_argument("--faker-baseline-count", type=int, default=5000)
    p.add_argument("--composite-count", type=int, default=2000)
    p.add_argument("--hard-neg-count", type=int, default=1000)
    args = p.parse_args()

    print("=" * 70)
    print("  PII NER v2 dataset preparation")
    print("=" * 70)

    rng = random.Random(42)
    random.seed(42)

    # ── load all sources ─────────────────────────────────
    klue_train = load_klue_split("train")
    klue_val = load_klue_split("validation")

    naver_train = parse_naver_ner(Path(__file__).parent / args.naver_data)

    wikiann_train = load_wikiann_split("train")
    wikiann_val = load_wikiann_split("validation")
    wikiann_test = load_wikiann_split("test")

    # faker (need korean_address module)
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from korean_address import load_admin_pairs
    addr_pairs = load_admin_pairs()

    org_pool = [
        "삼성전자", "LG전자", "SK하이닉스", "현대자동차", "기아", "포스코",
        "네이버", "카카오", "쿠팡", "네이버클라우드", "토스",
        "신한은행", "국민은행", "우리은행", "하나은행",
        "서울대학교", "연세대학교", "고려대학교", "한양대학교", "성균관대학교",
        "세브란스병원", "삼성서울병원", "아산병원", "서울대병원",
    ]

    print(f"\n  Generating Faker baseline ({args.faker_baseline_count})...")
    faker_base = generate_faker_baseline(args.faker_baseline_count, rng, addr_pairs, org_pool)
    print(f"    {len(faker_base)} samples")

    print(f"\n  Generating composite conjunctive ({args.composite_count})...")
    composite = generate_composite(args.composite_count, rng, addr_pairs, org_pool)
    print(f"    {len(composite)} samples")

    print(f"\n  Generating hard negatives ({args.hard_neg_count})...")
    hard_neg = generate_hard_negatives(args.hard_neg_count, rng)
    print(f"    {len(hard_neg)} samples")

    # ── combine ─────────────────────────────────────────
    all_train_pool = (
        klue_train + naver_train + wikiann_train
        + faker_base + composite + hard_neg
    )
    random.shuffle(all_train_pool)

    train, val, test = split_8_1_1(all_train_pool)

    print(f"\n{'='*70}")
    print(f"  Dataset Stats")
    print(f"{'='*70}")
    print(f"  Sources:")
    print(f"    klue_ner          {len(klue_train):>7,}")
    print(f"    naver_ner_2018    {len(naver_train):>7,}")
    print(f"    wikiann_ko        {len(wikiann_train):>7,}")
    print(f"    faker_baseline    {len(faker_base):>7,}")
    print(f"    faker_composite   {len(composite):>7,}")
    print(f"    hard_negative     {len(hard_neg):>7,}")
    print(f"    TOTAL train pool  {len(all_train_pool):>7,}")
    print()
    print(f"  Split:")
    print(f"    train             {len(train):>7,}")
    print(f"    val (internal)    {len(val):>7,}")
    print(f"    test (internal)   {len(test):>7,}")
    print()
    print(f"  External eval sets:")
    print(f"    klue_val          {len(klue_val):>7,}")
    print(f"    wikiann_val       {len(wikiann_val):>7,}")
    print(f"    wikiann_test      {len(wikiann_test):>7,}")
    print()
    print(f"  Train entity counts: {stats(train)}")

    # save
    out_path = Path(__file__).parent / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "label2id": LABEL2ID,
        "id2label": ID2LABEL,
        "train": train,
        "val": val,
        "test": test,
        "klue_val": klue_val,
        "wikiann_val": wikiann_val,
        "wikiann_test": wikiann_test,
        "meta": {
            "version": "v2",
            "klue_count": len(klue_train),
            "naver_count": len(naver_train),
            "wikiann_count": len(wikiann_train),
            "faker_baseline": len(faker_base),
            "faker_composite": len(composite),
            "hard_negative": len(hard_neg),
        },
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"\n[Saved] {out_path.resolve()} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
