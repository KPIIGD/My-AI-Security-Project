"""
v3 데이터 준비 — v1 setup 그대로 + composite/hard_neg augment만 추가.

v2 학습 실패 (KLUE F1 0.764 → 0.664) 후 conservative fix:
  - WikiAnn 제거 (영어 머신 라벨 quality 의심)
  - Naver NER 제거 (어절 라벨 char-level 변환 노이즈)
  - v1 성공 패턴 (KLUE + Faker baseline) 유지
  - 추가: Faker conjunctive composite 2k (v1 한계 보완)
  - 추가: hard negatives 1k (FP 방지)

총 ~34k (v1 31k 대비 약간 증가)
"""
from __future__ import annotations
import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

from datasets import load_dataset

PII_LABELS = ["O", "B-NAME", "I-NAME", "B-ADDRESS", "I-ADDRESS", "B-ORG", "I-ORG"]
LABEL2ID = {l: i for i, l in enumerate(PII_LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

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
    "지점 위치는 {address}.",
    "{name}님은 {org} 소속입니다.",
    "{org}에 입사했습니다.",
    "이번 회의는 {org} 본사에서 진행됩니다.",
    "{org}의 담당자는 {name}입니다.",
    "{name}({age}세)는 {address}에 거주하며 {org}에서 근무합니다.",
    "환자 {name}님 ({org} 소속)이 진료 받으셨습니다.",
    "{address}에 위치한 {org}로 방문하시면 됩니다.",
]

# v3 신규: conjunctive composite (v1 한계 보완)
COMPOSITE_TEMPLATES = [
    "저는 {name}이고 {address}에 거주합니다.",
    "저는 {name}이며 {org} 소속입니다.",
    "담당자는 {name}이고 {org}에서 일합니다.",
    "{name}이고 {org} 임원입니다.",
    "안녕하세요, 저는 {name}입니다. {address}에 살고 {org}에 다녀요.",
    "안녕하세요, {name}이라고 합니다. {org} 소속이고 {address}에 거주합니다.",
    "{name}과 {name2}가 {address}에서 만났습니다.",
    "{name}와 {org} 대표가 회의했습니다.",
    "{name}하고 {name2}이 같이 왔어요.",
    "{name}이랑 {org}에 다닙니다.",
    "{name}가 {address}에서 일합니다.",
    "{name}이 {address}로 이사갔습니다.",
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
    "{abstract}이 모두에게 필요합니다.",
    "고객센터 대표번호는 1588-{4d}입니다.",
    "예시 전화번호는 010-0000-0000입니다.",
    "{weather}처럼 맑은 날이 좋아요.",
    "{abstract}이라는 단어는 자주 쓰입니다.",
    "{food}을 좋아하시나요?",
    "{abstract}을 추구하는 삶.",
    "{weather}이 아름답습니다.",
    "오늘 메뉴는 {food}입니다.",
    "이번 주말은 {abstract}에 대해 생각해보세요.",
]

WEATHER = ["하늘", "별", "햇빛", "구름", "바다", "산", "강", "노을", "달빛"]
ABSTRACT = ["사랑", "우정", "평화", "자유", "행복", "지혜", "용기", "정의", "신뢰", "희망"]
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


def gen_faker_baseline(count, rng, addr_pairs, org_pool):
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
            "source": "faker_baseline_v3",
        })
    return samples


def gen_composite(count, rng, addr_pairs, org_pool):
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
            "source": "faker_composite_v3",
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
            adj=rng.choice(["맑네요", "좋네요", "예쁘네요", "선선하네요", "푸르네요"]),
            **{"4d": f"{rng.randint(0,9999):04d}"},
        )
        chars = list(sentence)
        labels = ["O"] * len(chars)
        samples.append({
            "tokens": chars,
            "labels": [LABEL2ID[l] for l in labels],
            "label_names": labels,
            "sentence": sentence,
            "source": "hard_negative_v3",
        })
    return samples


def stats(samples):
    c = Counter()
    for s in samples:
        for lab in s["label_names"]:
            if lab.startswith("B-"):
                c[lab[2:]] += 1
    return dict(c)


def split_8_1_1(samples, seed=42):
    random.seed(seed)
    idx = list(range(len(samples)))
    random.shuffle(idx)
    n = len(idx)
    return ([samples[i] for i in idx[:int(n*0.8)]],
            [samples[i] for i in idx[int(n*0.8):int(n*0.9)]],
            [samples[i] for i in idx[int(n*0.9):]])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="../data/pii_ner_v3.json")
    p.add_argument("--faker-baseline", type=int, default=10000)
    p.add_argument("--composite", type=int, default=2000)
    p.add_argument("--hard-neg", type=int, default=1000)
    args = p.parse_args()

    print("=" * 70)
    print("  PII NER v3 dataset (conservative: v1 setup + augment)")
    print("=" * 70)

    rng = random.Random(42)
    random.seed(42)

    klue_train = load_klue_split("train")
    klue_val = load_klue_split("validation")

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

    print(f"\n  Generating Faker baseline ({args.faker_baseline})...")
    faker_base = gen_faker_baseline(args.faker_baseline, rng, addr_pairs, org_pool)
    print(f"    {len(faker_base)}")

    print(f"\n  Generating composite conjunctive ({args.composite})...")
    composite = gen_composite(args.composite, rng, addr_pairs, org_pool)
    print(f"    {len(composite)}")

    print(f"\n  Generating hard negatives ({args.hard_neg})...")
    hard_neg = gen_hard_neg(args.hard_neg, rng)
    print(f"    {len(hard_neg)}")

    all_train = klue_train + faker_base + composite + hard_neg
    random.shuffle(all_train)
    train, val, test = split_8_1_1(all_train)

    print(f"\n{'='*70}")
    print(f"  Stats")
    print(f"{'='*70}")
    print(f"  Total pool: {len(all_train):>6,}")
    print(f"    klue_train       {len(klue_train):>6,}")
    print(f"    faker_baseline   {len(faker_base):>6,}")
    print(f"    faker_composite  {len(composite):>6,}")
    print(f"    hard_negative    {len(hard_neg):>6,}")
    print()
    print(f"  Train: {len(train):>6,} | entities: {stats(train)}")
    print(f"  Val:   {len(val):>6,}")
    print(f"  Test:  {len(test):>6,}")
    print(f"  KLUE val (external): {len(klue_val):>6,}")

    data = {
        "label2id": LABEL2ID,
        "id2label": ID2LABEL,
        "train": train,
        "val": val,
        "test": test,
        "klue_test": klue_val,  # train.py v1 호환을 위해 klue_test key
        "meta": {
            "version": "v3",
            "klue": len(klue_train),
            "faker_baseline": len(faker_base),
            "composite": len(composite),
            "hard_negative": len(hard_neg),
        },
    }
    out = Path(__file__).parent / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    size_mb = out.stat().st_size / 1024 / 1024
    print(f"\n[Saved] {out.resolve()} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
