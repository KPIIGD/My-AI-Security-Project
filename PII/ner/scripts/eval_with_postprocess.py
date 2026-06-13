"""
W2 작업 — Leo97 + ADDRESS 후처리 후 재평가.

ADDRESS span의 핵심 문제:
  KLUE-NER이 "서울"/"강남구"/"역삼동" 별도 출력 → gold는 "서울특별시 강남구 ..." full span
  → pipeline 결과를 후처리로 병합해야 span-exact F1 ↑

비교:
  - baseline: pipeline 그대로
  - + addr_merge: 인접 ADDRESS span 병합
  - + name_strip: NAME 조사·호칭 분리 (suffix)
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

import torch
from transformers import pipeline
from datasets import load_dataset


CKPT = "Leo97/KoELECTRA-small-v3-modu-ner"
MAX_SAMPLES = 200

ENTITY_TO_PII = {
    "PS": "NAME", "LC": "ADDRESS", "OG": "ORG",
}


def map_pred(entity_group: str) -> str | None:
    return ENTITY_TO_PII.get(entity_group)


def build_gold_spans(sample, label_names) -> set[tuple]:
    """KLUE-NER char-level BIO → (start, end, type) char offset spans."""
    tokens = sample["tokens"]
    tags = sample["ner_tags"]
    spans = []
    cur_start, cur_type = None, None
    char_pos = 0

    for char, tag_id in zip(tokens, tags):
        tag = label_names[tag_id]
        bare = tag[2:] if tag.startswith(("B-", "I-")) else tag
        pii_type = ENTITY_TO_PII.get(bare)

        if tag.startswith("B-"):
            if cur_start is not None:
                spans.append((cur_start, char_pos, cur_type))
            cur_start, cur_type = (char_pos, pii_type) if pii_type else (None, None)
        elif tag == "O" or pii_type is None:
            if cur_start is not None:
                spans.append((cur_start, char_pos, cur_type))
                cur_start, cur_type = None, None

        char_pos += len(char)

    if cur_start is not None:
        spans.append((cur_start, char_pos, cur_type))

    return {s for s in spans if s[2] in {"NAME", "ADDRESS", "ORG"}}


def merge_address_spans(spans: list[tuple], sentence: str, max_gap: int = 5) -> list[tuple]:
    """인접 ADDRESS span 병합 (mapping_rules.py 로직 inline)."""
    if not spans:
        return spans
    addr = sorted([s for s in spans if s[2] == "ADDRESS"], key=lambda s: s[0])
    other = [s for s in spans if s[2] != "ADDRESS"]
    if not addr:
        return spans

    merged = []
    cs, ce, ct = addr[0]
    for s, e, t in addr[1:]:
        gap = sentence[ce:s]
        if len(gap.strip()) <= max_gap and not any(c in gap for c in ".!?\n"):
            ce = e
        else:
            merged.append((cs, ce, ct))
            cs, ce, ct = s, e, t
    merged.append((cs, ce, ct))
    return other + merged


import re
JOSA = re.compile(r"(이가|에게서|로부터|에게|에서|으로|와|과|은|는|을|를|이|가|로|의|만)$")
HONORIFIC = re.compile(r"(님|씨|선생님|교수님|박사님|사장님|이사님)$")


def strip_name_suffix(spans: list[tuple], sentence: str) -> list[tuple]:
    """NAME span 끝의 조사·호칭 분리 (span end 줄임)."""
    new_spans = []
    for s, e, t in spans:
        if t != "NAME":
            new_spans.append((s, e, t))
            continue
        text = sentence[s:e]
        for pat in (HONORIFIC, JOSA):
            m = pat.search(text)
            if m:
                e -= len(m.group(0))
                break
        new_spans.append((s, e, t))
    return new_spans


def predict_spans(nlp, sentence: str) -> list[tuple]:
    pred = nlp(sentence)
    spans = []
    for ent in pred:
        pii = map_pred(ent["entity_group"])
        if pii:
            spans.append((int(ent["start"]), int(ent["end"]), pii))
    return spans


def f1_per_class(pred_set: set, gold_set: set, classes=("NAME", "ADDRESS", "ORG")):
    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    for sp in pred_set & gold_set:
        tp[sp[2]] += 1
    for sp in pred_set - gold_set:
        fp[sp[2]] += 1
    for sp in gold_set - pred_set:
        fn[sp[2]] += 1
    out = {}
    macro = 0.0
    for c in classes:
        p = tp[c] / (tp[c] + fp[c]) if tp[c] + fp[c] > 0 else 0.0
        r = tp[c] / (tp[c] + fn[c]) if tp[c] + fn[c] > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        out[c] = {"P": round(p, 3), "R": round(r, 3), "F1": round(f1, 3),
                  "tp": tp[c], "fp": fp[c], "fn": fn[c]}
        macro += f1
    out["macro_F1"] = round(macro / len(classes), 3)
    return out


def main():
    print(f"Loading KLUE-NER dev ({MAX_SAMPLES} samples) and {CKPT}...")
    ds = load_dataset("klue", "ner", split="validation")
    label_names = ds.features["ner_tags"].feature.names
    samples = list(ds)[:MAX_SAMPLES]

    device = 0 if torch.cuda.is_available() else -1
    nlp = pipeline("ner", model=CKPT, tokenizer=CKPT,
                   device=device, aggregation_strategy="simple")

    # 3가지 모드로 동일 데이터 평가
    mode_pred_sets = {
        "baseline": [],
        "+ addr_merge": [],
        "+ addr_merge + name_strip": [],
    }
    gold_sets = []

    print("\nRunning predictions + 3-stage post-processing...")
    for i, sample in enumerate(samples):
        sentence = "".join(sample["tokens"])
        gold = build_gold_spans(sample, label_names)
        gold_sets.append(gold)

        # baseline
        baseline = set(predict_spans(nlp, sentence))
        mode_pred_sets["baseline"].append(baseline)

        # + addr_merge
        merged = set(merge_address_spans(list(baseline), sentence))
        mode_pred_sets["+ addr_merge"].append(merged)

        # + addr_merge + name_strip
        stripped = set(strip_name_suffix(list(merged), sentence))
        mode_pred_sets["+ addr_merge + name_strip"].append(stripped)

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{MAX_SAMPLES}")

    # 메트릭 계산 (mode별)
    results = {}
    print(f"\n\n{'='*78}")
    print(f"  Leo97 + 후처리 단계별 결과 (KLUE-NER dev × {MAX_SAMPLES})")
    print(f"{'='*78}")
    print(f"  {'Mode':<32} {'NAME-F1':<10} {'ADDR-F1':<10} {'ORG-F1':<10} {'macro':<10}")
    print(f"  {'-'*32} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

    for mode, pred_list in mode_pred_sets.items():
        all_pred = set()
        all_gold = set()
        for ps, gs in zip(pred_list, gold_sets):
            for sp in ps:
                all_pred.add((id(ps), *sp))  # tag with sample id to avoid cross-sample dedup
            for sp in gs:
                all_gold.add((id(gs), *sp))

        # 위 방식이 dedup 깨지므로 sample별로 계산 후 합산하는 방식으로
        tp_all = defaultdict(int)
        fp_all = defaultdict(int)
        fn_all = defaultdict(int)
        for ps, gs in zip(pred_list, gold_sets):
            for sp in ps & gs:
                tp_all[sp[2]] += 1
            for sp in ps - gs:
                fp_all[sp[2]] += 1
            for sp in gs - ps:
                fn_all[sp[2]] += 1

        out = {}
        macro = 0
        for c in ("NAME", "ADDRESS", "ORG"):
            p = tp_all[c] / (tp_all[c] + fp_all[c]) if tp_all[c] + fp_all[c] > 0 else 0.0
            r = tp_all[c] / (tp_all[c] + fn_all[c]) if tp_all[c] + fn_all[c] > 0 else 0.0
            f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
            out[c] = {"P": round(p, 3), "R": round(r, 3), "F1": round(f1, 3)}
            macro += f1
        out["macro_F1"] = round(macro / 3, 3)
        results[mode] = out

        print(f"  {mode:<32} {out['NAME']['F1']:<10.3f} {out['ADDRESS']['F1']:<10.3f} "
              f"{out['ORG']['F1']:<10.3f} {out['macro_F1']:<10.3f}")

    # Verdict
    final_macro = results["+ addr_merge + name_strip"]["macro_F1"]
    print(f"\n{'='*78}")
    if final_macro >= 0.75:
        print(f"  ✅ A-primary 확정 — Leo97 + 후처리, macro-F1 = {final_macro}")
    elif final_macro >= 0.60:
        print(f"  ⚠ Leo97 + 후처리만으론 부족 (macro-F1 = {final_macro})")
        print(f"     → ADDRESS-only mini fine-tune 또는 사전 보강 추가 필요")
    else:
        print(f"  ❌ C-fallback 발동 (macro-F1 = {final_macro})")

    out_path = Path(__file__).parent / "../reports/eval_with_postprocess.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"\n📁 Saved: {out_path.resolve()}")


if __name__ == "__main__":
    main()
