"""
W2 화 EOD deadline — A-primary 후보 정량 평가 (수정판).

이전 버그 fix:
1. monologg는 "PER-B" suffix style → BIO detection 양쪽 다 처리
2. KLUE-NER tokens는 char 단위 → sentence 단위 inference + char offset 비교
3. pipeline + aggregation_strategy="simple"로 BIO + subword 자동 처리

기준:
- macro-F1 ≥ 0.75 → A-primary 확정
- 0.60 ~ 0.75 → 후처리 1일 시도
- < 0.60 → C-fallback 발동
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

import torch
from transformers import pipeline
from datasets import load_dataset


CANDIDATES = {
    "monologg": "monologg/koelectra-base-v3-naver-ner",
    "leo97": "Leo97/KoELECTRA-small-v3-modu-ner",
}

# 모델별 entity_group → PII 라벨 매핑
# pipeline aggregation_strategy="simple"이 BIO 접두/접미 자동 제거
ENTITY_TO_PII = {
    # Naver NER (monologg) — entity_group이 "PER", "LOC", "ORG", "CVL" 등
    "PER": "NAME",
    "LOC": "ADDRESS",
    "ORG": "ORG",
    # 모두의 말뭉치 (Leo97) — entity_group이 "PS", "LC", "OG" 등
    "PS": "NAME",
    "LC": "ADDRESS",
    "OG": "ORG",
}


def map_pred_label(entity_group: str) -> str | None:
    """pipeline output의 entity_group → PII 라벨 (NAME/ADDRESS/ORG) or None."""
    return ENTITY_TO_PII.get(entity_group)


def build_gold_spans(sample, label_names) -> set[tuple]:
    """KLUE-NER char-level BIO → char-offset (start, end, pii_type) span set."""
    tokens = sample["tokens"]   # 문자 리스트
    tags = sample["ner_tags"]   # BIO 라벨 ID 리스트
    spans = []
    cur_start = None
    cur_type = None
    char_pos = 0

    for char, tag_id in zip(tokens, tags):
        tag = label_names[tag_id]
        if tag.startswith(("B-", "I-")):
            bare = tag[2:]
        else:
            bare = tag
        pii_type = ENTITY_TO_PII.get(bare)

        if tag.startswith("B-"):
            if cur_start is not None:
                spans.append((cur_start, char_pos, cur_type))
            if pii_type:
                cur_start = char_pos
                cur_type = pii_type
            else:
                cur_start = None
                cur_type = None
        elif tag == "O" or pii_type is None:
            if cur_start is not None:
                spans.append((cur_start, char_pos, cur_type))
                cur_start = None
                cur_type = None
        # I-: same type, continue

        char_pos += len(char)

    if cur_start is not None:
        spans.append((cur_start, char_pos, cur_type))

    return {s for s in spans if s[2] in {"NAME", "ADDRESS", "ORG"}}


def evaluate(name: str, ckpt: str, samples, label_names, max_samples: int = 200) -> dict:
    print(f"\n{'='*70}")
    print(f"  [{name.upper()}] {ckpt} on KLUE-NER dev × {max_samples}")
    print(f"{'='*70}")

    device = 0 if torch.cuda.is_available() else -1
    print(f"  Loading pipeline (device={'cuda' if device==0 else 'cpu'})...")
    nlp = pipeline("ner", model=ckpt, tokenizer=ckpt,
                   device=device, aggregation_strategy="simple")

    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    n = min(max_samples, len(samples))

    for i, sample in enumerate(samples[:n]):
        sentence = "".join(sample["tokens"])  # char 리스트 → 문자열

        # gold spans (char offset)
        gold_spans = build_gold_spans(sample, label_names)

        # pred spans
        try:
            pred_entities = nlp(sentence)
        except Exception as e:
            print(f"  [WARN] sample {i}: {e}")
            continue

        pred_spans = set()
        for ent in pred_entities:
            pii_type = map_pred_label(ent["entity_group"])
            if pii_type is not None:
                pred_spans.add((int(ent["start"]), int(ent["end"]), pii_type))

        # span-exact 비교
        for sp in pred_spans & gold_spans:
            tp[sp[2]] += 1
        for sp in pred_spans - gold_spans:
            fp[sp[2]] += 1
        for sp in gold_spans - pred_spans:
            fn[sp[2]] += 1

        if (i + 1) % 50 == 0:
            print(f"  ... {i+1}/{n}")

    # 메트릭
    metrics = {}
    macro_f1 = 0.0
    classes = ["NAME", "ADDRESS", "ORG"]
    for cls in classes:
        p = tp[cls] / (tp[cls] + fp[cls]) if tp[cls] + fp[cls] > 0 else 0.0
        r = tp[cls] / (tp[cls] + fn[cls]) if tp[cls] + fn[cls] > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        metrics[cls] = {"precision": round(p, 3), "recall": round(r, 3),
                        "f1": round(f1, 3),
                        "tp": tp[cls], "fp": fp[cls], "fn": fn[cls]}
        macro_f1 += f1
    macro_f1 /= len(classes)
    metrics["macro_f1"] = round(macro_f1, 3)

    print(f"\n  Per-class span-exact F1:")
    for cls in classes:
        m = metrics[cls]
        print(f"    {cls:<10} P={m['precision']:.3f}  R={m['recall']:.3f}  "
              f"F1={m['f1']:.3f}  (tp={m['tp']}, fp={m['fp']}, fn={m['fn']})")
    print(f"\n  ★ macro-F1 = {macro_f1:.3f}")

    if macro_f1 >= 0.75:
        verdict = "✅ A-primary 확정 가능 (macro-F1 ≥ 0.75)"
    elif macro_f1 >= 0.60:
        verdict = "⚠️  ADDRESS 후처리 1일 시도 후 재측정 (0.60~0.75)"
    else:
        verdict = "❌ C-fallback 즉시 발동 권고 (< 0.60)"
    print(f"\n  Verdict: {verdict}")

    return {"name": name, "ckpt": ckpt, "metrics": metrics, "verdict": verdict}


def main():
    print("Loading KLUE-NER dev set...")
    ds = load_dataset("klue", "ner", split="validation")
    print(f"  loaded {len(ds)} examples")

    # KLUE-NER label names (정수 ID → 라벨 문자열)
    label_names = ds.features["ner_tags"].feature.names
    print(f"  label_names: {label_names}")

    samples = list(ds)

    results = []
    for name, ckpt in CANDIDATES.items():
        try:
            r = evaluate(name, ckpt, samples, label_names, max_samples=200)
            results.append(r)
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append({"name": name, "ckpt": ckpt, "error": str(e)})

    # 비교
    print(f"\n\n{'='*70}")
    print("  최종 비교")
    print(f"{'='*70}")
    print(f"  {'모델':<12} {'NAME-F1':<10} {'ADDR-F1':<10} {'ORG-F1':<10} {'macro-F1':<10}")
    for r in results:
        if "metrics" in r:
            m = r["metrics"]
            print(f"  {r['name']:<12} "
                  f"{m['NAME']['f1']:<10.3f} "
                  f"{m['ADDRESS']['f1']:<10.3f} "
                  f"{m['ORG']['f1']:<10.3f} "
                  f"{m['macro_f1']:<10.3f}")

    out_path = Path(__file__).parent / "../reports/eval_checkpoints.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"\n📁 Saved: {out_path.resolve()}")


if __name__ == "__main__":
    main()
