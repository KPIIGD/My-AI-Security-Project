# -*- coding: utf-8 -*-
"""KLUE-NER val 에서 v3 ONNX INT8 모델의 per-entity F1 분해.

목적 (task #2): macro-F1 0.766 / micro-F1 0.792 가 어디서 깎이는지 카테고리별 찍기.
NAME / ADDRESS / ORG 중 어느 entity 가 약점인지 + precision/recall 분리 분석 → v4 데이터
우선순위 결정 근거.

입력: KLUE-NER val (5,000 문장)
모델: models/pii_ner_v3/onnx_int8/model.onnx (322MB)
출력: reports/klue_per_entity_v3.json + stdout classification_report

실행: python scripts/eval_klue_per_entity.py
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
from collections import Counter

import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
from seqeval.metrics import classification_report, f1_score


ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models" / "pii_ner_v3" / "onnx_int8"
TOKENIZER_DIR = ROOT / "models" / "pii_ner_v3" / "final"
LABEL_MAP_PATH = ROOT / "models" / "pii_ner_v3" / "final" / "label_map.json"
# data/pii_ner_v3.json['klue_test'] = KLUE val 5,000 (이미 PII 스키마로 매핑됨)
DATA_PATH = ROOT / "data" / "pii_ner_v3.json"
OUT_PATH = ROOT / "reports" / "klue_per_entity_v3.json"

MAX_LENGTH = 128


def load_labels():
    with LABEL_MAP_PATH.open(encoding="utf-8") as f:
        m = json.load(f)
    id_to_label = {int(k): v for k, v in m["id_to_label"].items()}
    return id_to_label


def load_klue_val():
    """data/pii_ner_v3.json['klue_test'] 5,000 샘플 (이미 PII 스키마)."""
    with DATA_PATH.open(encoding="utf-8") as f:
        d = json.load(f)
    return d["klue_test"], d["label2id"]


def run_inference(session, tokenizer, char_tokens, max_length=MAX_LENGTH):
    """char-level token list → ONNX 추론 → (word-aligned pred, char index) 쌍.

    tokenizer 가 공백/특수 char 를 skip 하면 word_ids 에서 해당 char idx 가 빠짐.
    gold 추출 시 같은 char idx 만 사용해야 길이/의미 일치 (학습 코드와 동일).
    """
    enc = tokenizer(
        char_tokens,
        is_split_into_words=True,
        truncation=True,
        max_length=max_length,
        return_tensors="np",
    )
    inputs = {
        "input_ids": enc["input_ids"].astype(np.int64),
        "attention_mask": enc["attention_mask"].astype(np.int64),
    }
    if "token_type_ids" in [inp.name for inp in session.get_inputs()]:
        inputs["token_type_ids"] = enc.get(
            "token_type_ids", np.zeros_like(enc["input_ids"])
        ).astype(np.int64)

    outputs = session.run(None, inputs)
    logits = outputs[0][0]
    pred_ids = logits.argmax(axis=-1)

    word_ids = enc.word_ids(batch_index=0)
    aligned_preds = []
    aligned_char_indices = []
    prev = None
    for i, wid in enumerate(word_ids):
        if wid is None:
            continue
        if wid != prev:
            aligned_preds.append(int(pred_ids[i]))
            aligned_char_indices.append(int(wid))
        prev = wid
    return aligned_preds, aligned_char_indices


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="평가 샘플 수 (0=전체 5000)")
    ap.add_argument("--out-suffix", default="", help="출력 파일 suffix (예: _500)")
    args = ap.parse_args()

    print(f"Loading ONNX INT8 model from {MODEL_DIR}...")
    so = ort.SessionOptions()
    so.intra_op_num_threads = 4
    session = ort.InferenceSession(str(MODEL_DIR / "model.onnx"), so)
    print(f"  inputs: {[i.name for i in session.get_inputs()]}")
    print(f"  outputs: {[o.name for o in session.get_outputs()]}")

    print(f"\nLoading tokenizer from {TOKENIZER_DIR}...")
    tokenizer = AutoTokenizer.from_pretrained(str(TOKENIZER_DIR))

    id_to_label = load_labels()
    print(f"  labels: {list(id_to_label.values())}")

    print(f"\nLoading KLUE-NER val from local cache ({DATA_PATH})...")
    ds, label2id = load_klue_val()
    if args.limit > 0:
        ds = ds[:args.limit]
        print(f"  [LIMIT] using first {len(ds)} samples")
    print(f"  sentences: {len(ds)}")
    print(f"  label2id: {label2id}")

    true_seqs = []
    pred_seqs = []

    print(f"\nRunning inference on {len(ds)} sentences...")
    t0 = time.time()
    for i, sample in enumerate(ds):
        chars = sample["tokens"]
        gold_pii_full = sample["label_names"]  # 이미 PII BIO, char 단위

        pred_ids, char_indices = run_inference(session, tokenizer, chars)
        if not pred_ids:
            continue
        pred_pii = [id_to_label[p] for p in pred_ids]
        # gold 도 word_ids 에 등장한 char idx 만 추출 (mismatch 차단)
        gold_pii = [gold_pii_full[ci] for ci in char_indices if ci < len(gold_pii_full)]
        min_len = min(len(gold_pii), len(pred_pii))
        if min_len == 0:
            continue
        true_seqs.append(gold_pii[:min_len])
        pred_seqs.append(pred_pii[:min_len])

        if (i + 1) % 500 == 0:
            elapsed = time.time() - t0
            print(f"  {i+1}/{len(ds)} | elapsed {elapsed:.1f}s")

    elapsed = time.time() - t0
    print(f"\nInference done in {elapsed:.1f}s ({elapsed/len(ds)*1000:.1f}ms/sentence)")

    print("\n" + "=" * 70)
    print("Per-entity classification report (seqeval)")
    print("=" * 70)
    report = classification_report(true_seqs, pred_seqs, digits=4)
    print(report)

    # 숫자형으로도 dump
    report_dict = classification_report(true_seqs, pred_seqs, digits=4, output_dict=True)
    macro = f1_score(true_seqs, pred_seqs, average="macro")
    micro = f1_score(true_seqs, pred_seqs, average="micro")
    print(f"\nmacro-F1: {macro:.4f}")
    print(f"micro-F1: {micro:.4f}")

    # gold 분포 (왜 어떤 entity 가 underweight 인지 진단)
    gold_counts = Counter()
    for seq in true_seqs:
        for tag in seq:
            if tag.startswith("B-"):
                gold_counts[tag[2:]] += 1
    print(f"\nGold entity counts (B-tags): {dict(gold_counts)}")

    out_path = OUT_PATH.with_name(OUT_PATH.stem + args.out_suffix + OUT_PATH.suffix)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "model": "models/pii_ner_v3/onnx_int8/model.onnx",
        "eval_set": f"KLUE-NER validation ({len(ds)} sentences)",
        "per_entity": report_dict,
        "macro_f1": float(macro),
        "micro_f1": float(micro),
        "gold_entity_counts": dict(gold_counts),
        "inference_time_s": elapsed,
        "ms_per_sentence": elapsed / len(ds) * 1000,
    }
    # np.int/float → Python 기본형 변환 (JSON 직렬화)
    def _to_py(o):
        if isinstance(o, dict):
            return {k: _to_py(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_to_py(x) for x in o]
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        return o
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(_to_py(out), f, ensure_ascii=False, indent=2)
    print(f"\n[Saved] {out_path}")


if __name__ == "__main__":
    main()
