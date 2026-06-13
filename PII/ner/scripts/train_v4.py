"""
W2~W3 학습 — klue/bert-base + Phase 1/2 fine-tune.

Phase 1: encoder freeze, classifier head만 1 epoch (LR 5e-4)
Phase 2: 전체 unfreeze, 2 epoch (LR 2e-5, warmup 10%)

T4 16GB 기준:
- batch 16 (max_len 128) → 약 2~3시간
- batch 8 (max_len 256) → 약 4~5시간

사용:
  python train.py
  python train.py --base klue/roberta-base --output ../models/pii_ner_v1
  python train.py --epochs-phase2 3 --batch 32

Colab/Vast.ai 환경에서:
  !python train.py --output /content/drive/MyDrive/pii_ner_v1
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import torch
import numpy as np
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer, AutoModelForTokenClassification,
    Trainer, TrainingArguments, DataCollatorForTokenClassification
)


class PIINerDataset(Dataset):
    def __init__(self, samples, tokenizer, label2id, max_length=128):
        self.samples = samples
        self.tokenizer = tokenizer
        self.label2id = label2id
        self.max_length = max_length

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        tokens = s["tokens"]   # char 리스트
        labels = s["labels"]   # int 리스트 (LABEL2ID 기준)

        # char 단위 입력은 is_split_into_words=True로 처리
        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            max_length=self.max_length,
            padding=False,
        )
        word_ids = encoding.word_ids()

        # subword alignment: 첫 subword에만 라벨, 나머지는 -100
        aligned = []
        prev_wid = None
        for wid in word_ids:
            if wid is None:
                aligned.append(-100)
            elif wid != prev_wid:
                aligned.append(labels[wid] if wid < len(labels) else -100)
            else:
                aligned.append(-100)
            prev_wid = wid

        encoding["labels"] = aligned
        return encoding


def compute_metrics(eval_pred, id2label):
    """span-level entity F1 계산 (seqeval 사용)."""
    try:
        from seqeval.metrics import classification_report, f1_score
    except ImportError:
        print("[WARN] seqeval 미설치. 'pip install seqeval' 후 metric 정상 작동")
        return {"f1": 0.0}

    preds, labels = eval_pred
    preds = np.argmax(preds, axis=-1)

    true_labels, true_preds = [], []
    for p_seq, l_seq in zip(preds, labels):
        t_l, t_p = [], []
        for p, l in zip(p_seq, l_seq):
            if l != -100:
                t_l.append(id2label[l])
                t_p.append(id2label[p])
        if t_l:
            true_labels.append(t_l)
            true_preds.append(t_p)

    macro = f1_score(true_labels, true_preds, average="macro")
    micro = f1_score(true_labels, true_preds, average="micro")
    # v4 신규: per-entity F1 (NAME/ADDRESS/ORG) — task #2 진단 비교용
    out = {"macro_f1": macro, "micro_f1": micro}
    try:
        report = classification_report(true_labels, true_preds, digits=4, output_dict=True)
        for ent_type in ("NAME", "ADDRESS", "ORG"):
            if ent_type in report:
                out[f"f1_{ent_type}"] = report[ent_type]["f1-score"]
                out[f"precision_{ent_type}"] = report[ent_type]["precision"]
                out[f"recall_{ent_type}"] = report[ent_type]["recall"]
    except Exception:
        pass
    return out


def freeze_encoder(model, freeze: bool):
    """encoder 부분 freeze/unfreeze. Bert와 Electra 둘 다 처리."""
    encoder_attr = None
    for attr in ("bert", "electra", "roberta"):
        if hasattr(model, attr):
            encoder_attr = attr
            break

    if encoder_attr is None:
        # named_parameters로 fallback
        for name, p in model.named_parameters():
            if not name.startswith("classifier"):
                p.requires_grad = not freeze
    else:
        encoder = getattr(model, encoder_attr)
        for p in encoder.parameters():
            p.requires_grad = not freeze
        # classifier는 항상 학습 가능
        for p in model.classifier.parameters():
            p.requires_grad = True

    n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    n_total = sum(p.numel() for p in model.parameters())
    print(f"  Trainable: {n_trainable:,} / {n_total:,} "
          f"({100 * n_trainable / n_total:.1f}%)")


def main():
    p = argparse.ArgumentParser()
    # v4 default = v3 production setup (klue/roberta-large + Phase 1/2 + 5ep)
    # v3 TRAINING_RESULTS_v3.md §3 "v1 setup + minimal augment" 보호
    # v2 실패 (LWLR + FGM 동시 변경) 트랩 회피 — 본 스크립트엔 LWLR/FGM 없음
    p.add_argument("--base", default="klue/roberta-large",
                   help="베이스 모델. v3 production = klue/roberta-large")
    p.add_argument("--data", default="../data/pii_ner_v4.json")
    p.add_argument("--output", default="../models/pii_ner_v4")
    p.add_argument("--epochs-phase1", type=int, default=1)
    p.add_argument("--epochs-phase2", type=int, default=5)  # v3 = 5
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--max-length", type=int, default=128)
    p.add_argument("--lr-phase1", type=float, default=5e-4)
    p.add_argument("--lr-phase2", type=float, default=2e-5)
    p.add_argument("--warmup-ratio", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--klue-abort-threshold",
        type=float,
        default=0.0,
        help="v2 trap guard: 매 epoch klue_test macro-F1 < 임계값이면 즉시 학습 중단. "
             "0 = 비활성 (기본). v3 baseline 0.766 사용 권장. "
             "NEXT_SESSION.md '학습 중 확인 의무' 자동화.",
    )
    p.add_argument(
        "--klue-abort-log",
        default=None,
        help="--klue-abort-threshold 사용 시 각 epoch eval 결과를 append 할 JSONL. "
             "기본 = <output>/klue_epoch_log.jsonl",
    )
    args = p.parse_args()

    # 환경 정보
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n{'='*70}")
    print(f"  PII NER Fine-tune")
    print(f"{'='*70}")
    print(f"  Base model: {args.base}")
    print(f"  Device: {device}")
    if device == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name()}")
        print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # 데이터 로드
    data_path = Path(__file__).parent / args.data
    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    label2id = data["label2id"]
    id2label = {int(k): v for k, v in data["id2label"].items()}
    print(f"\n  Labels: {list(label2id.keys())}")
    print(f"  Train: {len(data['train'])}  Val: {len(data['val'])}  Test: {len(data['test'])}")

    # 모델 + 토크나이저
    print(f"\n  Loading {args.base}...")
    tokenizer = AutoTokenizer.from_pretrained(args.base)
    model = AutoModelForTokenClassification.from_pretrained(
        args.base,
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True,
    )

    # 데이터셋
    train_ds = PIINerDataset(data["train"], tokenizer, label2id, args.max_length)
    val_ds = PIINerDataset(data["val"], tokenizer, label2id, args.max_length)

    collator = DataCollatorForTokenClassification(tokenizer, return_tensors="pt")

    output_dir = Path(__file__).parent / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    # ─────────────────────────────────────────────
    # Phase 1: encoder freeze, classifier head만
    # ─────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  Phase 1: encoder freeze, head only ({args.epochs_phase1} epoch, LR={args.lr_phase1})")
    print(f"{'='*70}")
    freeze_encoder(model, freeze=True)

    args1 = TrainingArguments(
        output_dir=str(output_dir / "phase1"),
        num_train_epochs=args.epochs_phase1,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch,
        learning_rate=args.lr_phase1,
        eval_strategy="epoch",
        save_strategy="no",
        logging_steps=50,
        report_to=[],
        seed=args.seed,
        fp16=(device == "cuda"),
    )

    trainer1 = Trainer(
        model=model,
        args=args1,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=collator,
        compute_metrics=lambda ep: compute_metrics(ep, id2label),
    )
    trainer1.train()

    # ─────────────────────────────────────────────
    # Phase 2: 전체 unfreeze
    # ─────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  Phase 2: full unfreeze ({args.epochs_phase2} epoch, LR={args.lr_phase2})")
    print(f"{'='*70}")
    freeze_encoder(model, freeze=False)

    args2 = TrainingArguments(
        output_dir=str(output_dir / "phase2"),
        num_train_epochs=args.epochs_phase2,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch,
        learning_rate=args.lr_phase2,
        warmup_ratio=args.warmup_ratio,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        logging_steps=50,
        report_to=[],
        seed=args.seed,
        fp16=(device == "cuda"),
    )

    trainer2 = Trainer(
        model=model,
        args=args2,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=collator,
        compute_metrics=lambda ep: compute_metrics(ep, id2label),
    )

    # ── v2 trap guard: 매 epoch KLUE 외부 macro-F1 모니터 + 자동 중단 ──
    klue_abort_cb = None
    if args.klue_abort_threshold > 0 and data.get("klue_test"):
        from klue_abort_callback import KlueAbortCallback, attach_to_trainer
        klue_test_ds_for_cb = PIINerDataset(
            data["klue_test"], tokenizer, label2id, args.max_length
        )
        log_path = args.klue_abort_log or str(output_dir / "klue_epoch_log.jsonl")
        klue_abort_cb = KlueAbortCallback(
            klue_test_ds_for_cb,
            threshold=args.klue_abort_threshold,
            log_path=log_path,
        )
        attach_to_trainer(klue_abort_cb, trainer2)
        print(
            f"\n[v2 Trap Guard] KLUE 외부 macro-F1 < {args.klue_abort_threshold:.4f} "
            f"이면 즉시 학습 중단. epoch log → {log_path}"
        )

    trainer2.train()

    if klue_abort_cb is not None and klue_abort_cb.aborted:
        # v3 백업 보호: aborted run 은 final/ 디렉터리에 덮어쓰지 않고 종료.
        print("\n[v2 Trap Guard] 학습이 가드로 중단됨. final 저장 스킵.")
        abort_summary = {
            "aborted": True,
            "threshold": klue_abort_cb.threshold,
            "history": klue_abort_cb.history,
        }
        with (output_dir / "ABORTED.json").open("w", encoding="utf-8") as f:
            json.dump(abort_summary, f, ensure_ascii=False, indent=2)
        print(f"  abort summary → {output_dir / 'ABORTED.json'}")
        return

    # ─────────────────────────────────────────────
    # 최종 저장 + 평가
    # ─────────────────────────────────────────────
    final_path = output_dir / "final"
    trainer2.save_model(str(final_path))
    tokenizer.save_pretrained(str(final_path))
    print(f"\n[Saved] Final model: {final_path}")

    # Test 평가
    if data["test"]:
        print(f"\n  Final test eval ({len(data['test'])} samples)...")
        test_ds = PIINerDataset(data["test"], tokenizer, label2id, args.max_length)
        test_metrics = trainer2.evaluate(test_ds, metric_key_prefix="test")
        print(f"  Test metrics: {test_metrics}")
        with (output_dir / "test_results.json").open("w", encoding="utf-8") as f:
            json.dump(test_metrics, f, ensure_ascii=False, indent=2)

    # KLUE-NER test (별도, in-distribution check)
    if data.get("klue_test"):
        print(f"\n  KLUE-NER test eval ({len(data['klue_test'])} samples)...")
        klue_test_ds = PIINerDataset(data["klue_test"], tokenizer, label2id, args.max_length)
        klue_metrics = trainer2.evaluate(klue_test_ds, metric_key_prefix="klue_test")
        print(f"  KLUE test metrics: {klue_metrics}")
        with (output_dir / "klue_test_results.json").open("w", encoding="utf-8") as f:
            json.dump(klue_metrics, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
