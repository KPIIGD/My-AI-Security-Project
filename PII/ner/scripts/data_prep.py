"""
W2 데이터 준비 — KLUE-NER + Faker-ko → 통합 BIO 데이터셋.

출력 라벨 (3 클래스 + O = BIO 7-tag):
  O, B-NAME, I-NAME, B-ADDRESS, I-ADDRESS, B-ORG, I-ORG

데이터 소스:
  1. KLUE-NER train 21,008건 (PS/LC/OG → NAME/ADDR/ORG, 나머지는 O)
  2. Faker-ko 합성 1만 (PII 도메인 보강)

분할:
  - 문서 단위 8:1:1 (data leakage 차단)
  - augmentation은 분할 후 적용

사용:
  python data_prep.py --output ../data/pii_ner_v1.json
  python data_prep.py --synth-count 10000 --output ../data/pii_ner_v1_with_synth.json
"""
from __future__ import annotations
import argparse
import json
import random
from collections import Counter
from pathlib import Path

from datasets import load_dataset

# 라벨 매핑
KLUE_TO_PII = {
    "B-PS": "B-NAME", "I-PS": "I-NAME",
    "B-LC": "B-ADDRESS", "I-LC": "I-ADDRESS",
    "B-OG": "B-ORG", "I-OG": "I-ORG",
    # 나머지(B-DT, B-TI, B-QT)는 O로
}

PII_LABELS = ["O", "B-NAME", "I-NAME", "B-ADDRESS", "I-ADDRESS", "B-ORG", "I-ORG"]
LABEL2ID = {l: i for i, l in enumerate(PII_LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}


def convert_klue_sample(sample, label_names) -> dict:
    """KLUE-NER sample → PII labeled sample.

    KLUE는 char 단위 토큰 + ner_tags. PII 라벨로 변환 후 char 시퀀스 그대로 유지.
    """
    chars = sample["tokens"]
    klue_tags = [label_names[t] for t in sample["ner_tags"]]
    pii_tags = [KLUE_TO_PII.get(t, "O") for t in klue_tags]
    return {
        "tokens": chars,                                # char 단위 그대로
        "labels": [LABEL2ID[t] for t in pii_tags],
        "label_names": pii_tags,
        "sentence": "".join(chars),
        "source": "klue_ner",
    }


def load_klue_ner_split(split: str = "train") -> list[dict]:
    """KLUE-NER split 로드 + PII 라벨 변환."""
    print(f"  Loading KLUE-NER {split}...")
    ds = load_dataset("klue", "ner", split=split)
    label_names = ds.features["ner_tags"].feature.names
    samples = [convert_klue_sample(s, label_names) for s in ds]
    print(f"    {len(samples)} samples")
    return samples


# ─────────────────────────────────────────────────────────
# Faker-ko 합성 데이터 생성
# ─────────────────────────────────────────────────────────

# PII 합성 템플릿 (NAME/ADDRESS/ORG 위주)
TEMPLATES = [
    # NAME 중심
    "안녕하세요, 저는 {name}입니다.",
    "{name}님께 연락드립니다.",
    "{name}이 등록하셨습니다.",
    "고객명: {name}, 가입일자는 어제입니다.",
    "담당자 {name} 과장님께 문의해 주세요.",
    "{name}씨가 방문 예정입니다.",

    # ADDRESS 중심
    "주소는 {address} 입니다.",
    "배송지: {address}",
    "{address}로 우편물을 보내주세요.",
    "{address}에 거주 중입니다.",
    "지점 위치는 {address}.",

    # ORG 중심
    "{name}님은 {org} 소속입니다.",
    "{org}에 입사했습니다.",
    "이번 회의는 {org} 본사에서 진행됩니다.",
    "{org}의 담당자는 {name}입니다.",

    # 복합
    "{name}({age}세)는 {address}에 거주하며 {org}에서 근무합니다.",
    "환자 {name}님 ({org} 소속)이 진료 받으셨습니다.",
    "{address}에 위치한 {org}로 방문하시면 됩니다.",
]


def generate_synthetic_samples(count: int = 10000, seed: int = 42) -> list[dict]:
    """Faker-ko 이름·ORG + 실 행정구역 데이터 기반 주소로 한국어 PII 합성.

    주소는 Faker의 fake.address()를 쓰지 않음 (이유: 시·도+시·군·구 무작위 조합·
    인명 포함 괄호 부속 텍스트로 ADDR span 오염). 대신 cosmosfarm/korea-administrative-district
    실 데이터 기반 합성기 (korean_address.py) 사용.
    """
    try:
        from faker import Faker
    except ImportError:
        print("  ⚠ faker 미설치. 'pip install faker' 후 재시도. 합성 0건으로 진행.")
        return []

    from korean_address import load_admin_pairs, random_address

    fake = Faker("ko_KR")
    Faker.seed(seed)
    random.seed(seed)        # main()의 random.shuffle 재현성용 (module state)
    rng = random.Random(seed)  # 합성 내부에서만 사용 (격리된 state)

    addr_pairs = load_admin_pairs()
    print(f"  Loaded {len(addr_pairs)} real (시·도, 시·군·구) pairs")

    # 한국 주요 ORG list (사전과 통합)
    org_pool = [
        "삼성전자", "LG전자", "SK하이닉스", "현대자동차", "기아", "포스코",
        "네이버", "카카오", "쿠팡", "네이버클라우드", "토스",
        "신한은행", "국민은행", "우리은행", "하나은행",
        "서울대학교", "연세대학교", "고려대학교", "한양대학교", "성균관대학교",
        "세브란스병원", "삼성서울병원", "아산병원", "서울대병원",
    ]

    samples = []
    for i in range(count):
        tmpl = rng.choice(TEMPLATES)
        name = fake.name()
        address = random_address(rng, addr_pairs)
        org = rng.choice(org_pool)
        age = rng.randint(20, 70)

        sentence = tmpl.format(name=name, address=address, org=org, age=age)

        # BIO 라벨링 (단순 substring 매칭)
        chars = list(sentence)
        labels = ["O"] * len(chars)

        for entity_text, entity_type in [(name, "NAME"), (address, "ADDRESS"), (org, "ORG")]:
            if entity_text in sentence:
                start = sentence.find(entity_text)
                end = start + len(entity_text)
                if labels[start] == "O":  # 이미 라벨된 곳은 skip
                    labels[start] = f"B-{entity_type}"
                    for j in range(start + 1, end):
                        if labels[j] == "O":
                            labels[j] = f"I-{entity_type}"

        samples.append({
            "tokens": chars,
            "labels": [LABEL2ID[l] for l in labels],
            "label_names": labels,
            "sentence": sentence,
            "source": "faker_ko",
        })

    print(f"  Generated {len(samples)} synthetic samples")
    return samples


# ─────────────────────────────────────────────────────────
# 분할 + 통계
# ─────────────────────────────────────────────────────────

def stats(samples: list[dict]) -> dict:
    """라벨별 entity 카운트."""
    counter = Counter()
    for s in samples:
        for lab in s["label_names"]:
            if lab.startswith("B-"):
                counter[lab[2:]] += 1
    return dict(counter)


def split_8_1_1(samples: list[dict], seed: int = 42) -> tuple[list, list, list]:
    """문서(=sample) 단위 8:1:1 분할."""
    random.seed(seed)
    indices = list(range(len(samples)))
    random.shuffle(indices)
    n = len(indices)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)
    train_idx = indices[:train_end]
    val_idx = indices[train_end:val_end]
    test_idx = indices[val_end:]
    return ([samples[i] for i in train_idx],
            [samples[i] for i in val_idx],
            [samples[i] for i in test_idx])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="../data/pii_ner_v1.json",
                   help="출력 파일 (json)")
    p.add_argument("--synth-count", type=int, default=10000,
                   help="Faker-ko 합성 데이터 수 (0이면 KLUE만)")
    p.add_argument("--include-klue-test", action="store_true",
                   help="KLUE-NER validation을 우리 test에 포함")
    args = p.parse_args()

    print("=" * 70)
    print("  PII NER 데이터셋 준비 v1")
    print("=" * 70)

    # 1. KLUE-NER train 로드 + PII 라벨 변환
    klue_train = load_klue_ner_split("train")

    # 2. Faker-ko 합성
    synth = []
    if args.synth_count > 0:
        print(f"\n  Generating Faker-ko synthetic ({args.synth_count})...")
        synth = generate_synthetic_samples(args.synth_count)

    # 3. 통합 + 8:1:1 분할
    all_samples = klue_train + synth
    random.shuffle(all_samples)
    train, val, test = split_8_1_1(all_samples)

    # 4. KLUE-NER validation을 별도 test로 (옵션)
    klue_test = []
    if args.include_klue_test:
        klue_test = load_klue_ner_split("validation")

    # 5. 통계
    print(f"\n{'='*70}")
    print(f"  Dataset Stats")
    print(f"{'='*70}")
    print(f"  Train: {len(train):>6}  | entities: {stats(train)}")
    print(f"  Val:   {len(val):>6}  | entities: {stats(val)}")
    print(f"  Test:  {len(test):>6}  | entities: {stats(test)}")
    if klue_test:
        print(f"  KLUE test (별도): {len(klue_test)} | entities: {stats(klue_test)}")

    # 6. 저장
    output = {
        "label2id": LABEL2ID,
        "id2label": ID2LABEL,
        "train": train,
        "val": val,
        "test": test,
        "klue_test": klue_test,
        "meta": {
            "klue_count": len(klue_train),
            "synth_count": len(synth),
            "total": len(all_samples),
        },
    }
    out_path = Path(__file__).parent / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=1)

    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"\n[Saved] {out_path.resolve()} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
