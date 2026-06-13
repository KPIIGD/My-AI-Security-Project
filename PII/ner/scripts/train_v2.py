"""
v2 학습 — 토론 합의 사항 반영:
  - Layer-wise LR decay 0.9
  - FGM Adversarial Training (epsilon=1.0)
  - External validation (KLUE val) 기준 early stopping
  - label smoothing 제거 (NER 역효과)
  - WikiAnn val/test, KLUE val 다중 평가

베이스: klue/roberta-large (v1과 동일)
데이터: pii_ner_v2.json (139k)

사용:
  python train_v2.py --batch 16 --epochs 5
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
    Trainer, TrainingArguments, DataCollatorForTokenClassification,
    EarlyStoppingCallback,
)


class PIINerDataset(Dataset):
    def __init__(self, samples, tokenizer, max_length=128):
        self.samples = samples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        tokens = s["tokens"]
        labels = s["labels"]

        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            max_length=self.max_length,
            padding=False,
        )
        word_ids = encoding.word_ids()
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
    from seqeval.metrics import f1_score
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
    return {"macro_f1": macro, "micro_f1": micro}


# ─────────────────────────────────────────────────────────
# Layer-wise LR decay
# ─────────────────────────────────────────────────────────
def get_layerwise_lr_groups(model, base_lr=2e-5, decay=0.9, weight_decay=0.01):
    """RoBERTa encoder layer-wise LR decay + classifier head 별도 LR.

    Top layer (classifier head): base_lr
    Last encoder layer: base_lr * decay^0
    First encoder layer: base_lr * decay^(num_layers - 1)
    Embeddings: base_lr * decay^num_layers
    """
    # encoder 이름 자동 감지
    encoder_name = None
    for attr in ("roberta", "bert", "electra"):
        if hasattr(model, attr):
            encoder_name = attr
            break

    if encoder_name is None:
        # fallback: single group
        return [{"params": list(model.parameters()), "lr": base_lr, "weight_decay": weight_decay}]

    encoder = getattr(model, encoder_name)
    num_layers = len(encoder.encoder.layer)
    no_decay_keywords = ("bias", "LayerNorm")
    groups = []

    # classifier
    classifier_params = [
        (n, p) for n, p in model.named_parameters()
        if not n.startswith(f"{encoder_name}.")
    ]
    classifier_decay = [p for n, p in classifier_params if not any(k in n for k in no_decay_keywords)]
    classifier_no_decay = [p for n, p in classifier_params if any(k in n for k in no_decay_keywords)]
    if classifier_decay:
        groups.append({"params": classifier_decay, "lr": base_lr, "weight_decay": weight_decay})
    if classifier_no_decay:
        groups.append({"params": classifier_no_decay, "lr": base_lr, "weight_decay": 0.0})

    # encoder layers (top-down)
    for layer_idx in range(num_layers):
        layer = encoder.encoder.layer[layer_idx]
        # Layer 0 = bottom, layer N-1 = top
        # We want top to get highest LR
        depth_from_top = num_layers - 1 - layer_idx
        lr = base_lr * (decay ** depth_from_top)
        params = list(layer.named_parameters())
        decay_p = [p for n, p in params if not any(k in n for k in no_decay_keywords)]
        no_decay_p = [p for n, p in params if any(k in n for k in no_decay_keywords)]
        if decay_p:
            groups.append({"params": decay_p, "lr": lr, "weight_decay": weight_decay})
        if no_decay_p:
            groups.append({"params": no_decay_p, "lr": lr, "weight_decay": 0.0})

    # embeddings (lowest)
    emb_lr = base_lr * (decay ** num_layers)
    emb_params = list(encoder.embeddings.named_parameters())
    emb_decay = [p for n, p in emb_params if not any(k in n for k in no_decay_keywords)]
    emb_no_decay = [p for n, p in emb_params if any(k in n for k in no_decay_keywords)]
    if emb_decay:
        groups.append({"params": emb_decay, "lr": emb_lr, "weight_decay": weight_decay})
    if emb_no_decay:
        groups.append({"params": emb_no_decay, "lr": emb_lr, "weight_decay": 0.0})

    return groups


# ─────────────────────────────────────────────────────────
# FGM Adversarial Training
# ─────────────────────────────────────────────────────────
class FGM:
    def __init__(self, model, epsilon=1.0):
        self.model = model
        self.epsilon = epsilon
        self.backup = {}

    def attack(self, emb_name="word_embeddings"):
        for name, param in self.model.named_parameters():
            if param.requires_grad and emb_name in name:
                self.backup[name] = param.data.clone()
                norm = torch.norm(param.grad)
                if norm != 0 and not torch.isnan(norm):
                    r_at = self.epsilon * param.grad / norm
                    param.data.add_(r_at)

    def restore(self, emb_name="word_embeddings"):
        for name, param in self.model.named_parameters():
            if param.requires_grad and emb_name in name:
                if name in self.backup:
                    param.data = self.backup[name]
        self.backup = {}


class FGMTrainer(Trainer):
    """Trainer with FGM adversarial training."""

    def __init__(self, *args, fgm_epsilon=1.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.fgm = FGM(self.model, epsilon=fgm_epsilon)

    def training_step(self, model, inputs, num_items_in_batch=None):
        # normal forward + backward
        model.train()
        inputs = self._prepare_inputs(inputs)
        with self.compute_loss_context_manager():
            loss = self.compute_loss(model, inputs)
        if self.args.gradient_accumulation_steps > 1:
            loss = loss / self.args.gradient_accumulation_steps
        loss.backward()

        # FGM perturb
        self.fgm.attack()
        with self.compute_loss_context_manager():
            adv_loss = self.compute_loss(model, inputs)
        if self.args.gradient_accumulation_steps > 1:
            adv_loss = adv_loss / self.args.gradient_accumulation_steps
        adv_loss.backward()
        self.fgm.restore()

        return loss.detach()


# ─────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="klue/roberta-large")
    p.add_argument("--data", default="../data/pii_ner_v2.json")
    p.add_argument("--output", default="../models/pii_ner_v2")
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--max-length", type=int, default=128)
    p.add_argument("--base-lr", type=float, default=2e-5)
    p.add_argument("--layerwise-decay", type=float, default=0.9)
    p.add_argument("--fgm-epsilon", type=float, default=1.0)
    p.add_argument("--warmup-ratio", type=float, default=0.1)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--early-stop-patience", type=int, default=2)
    args = p.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n{'='*70}")
    print(f"  PII NER v2 Fine-tune")
    print(f"{'='*70}")
    print(f"  Base: {args.base}")
    print(f"  Device: {device}")
    if device == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name()}")
        print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    print(f"  Layer-wise LR decay: {args.layerwise_decay}")
    print(f"  FGM epsilon: {args.fgm_epsilon}")
    print(f"  Base LR: {args.base_lr}")

    # load
    data_path = Path(__file__).parent / args.data
    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    label2id = data["label2id"]
    id2label = {int(k): v for k, v in data["id2label"].items()}
    print(f"\n  Labels: {list(label2id.keys())}")
    print(f"  Train: {len(data['train']):,}  Val: {len(data['val']):,}  Test: {len(data['test']):,}")
    print(f"  External: KLUE val {len(data['klue_val']):,}, "
          f"WikiAnn val {len(data['wikiann_val']):,}, test {len(data['wikiann_test']):,}")

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    model = AutoModelForTokenClassification.from_pretrained(
        args.base,
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True,
    )

    # datasets
    train_ds = PIINerDataset(data["train"], tokenizer, args.max_length)
    klue_val_ds = PIINerDataset(data["klue_val"], tokenizer, args.max_length)

    collator = DataCollatorForTokenClassification(tokenizer, return_tensors="pt")
    output_dir = Path(__file__).parent / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    # layer-wise LR groups
    optimizer_grouped_params = get_layerwise_lr_groups(
        model, base_lr=args.base_lr, decay=args.layerwise_decay,
        weight_decay=args.weight_decay,
    )
    optimizer = torch.optim.AdamW(optimizer_grouped_params)
    # scheduler 자동 (HF Trainer가 default linear + warmup)

    training_args = TrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch * 2,  # eval은 더 크게
        learning_rate=args.base_lr,  # ignored (we use custom optimizer)
        warmup_ratio=args.warmup_ratio,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        logging_steps=100,
        report_to=[],
        seed=args.seed,
        fp16=(device == "cuda"),
    )

    # FGM + fp16 호환 이슈 회피 — fgm_epsilon > 0 인 경우만 FGM 사용
    if args.fgm_epsilon > 0:
        trainer = FGMTrainer(
            model=model,
            args=training_args,
            train_dataset=train_ds,
            eval_dataset=klue_val_ds,
            tokenizer=tokenizer,
            data_collator=collator,
            compute_metrics=lambda ep: compute_metrics(ep, id2label),
            callbacks=[EarlyStoppingCallback(early_stopping_patience=args.early_stop_patience)],
            optimizers=(optimizer, None),
            fgm_epsilon=args.fgm_epsilon,
        )
    else:
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_ds,
            eval_dataset=klue_val_ds,  # ← external val for early stop
            tokenizer=tokenizer,
            data_collator=collator,
            compute_metrics=lambda ep: compute_metrics(ep, id2label),
            callbacks=[EarlyStoppingCallback(early_stopping_patience=args.early_stop_patience)],
            optimizers=(optimizer, None),
        )

    print(f"\n{'='*70}\n  Training...\n{'='*70}")
    trainer.train()

    # save final
    final_path = output_dir / "final"
    trainer.save_model(str(final_path))
    tokenizer.save_pretrained(str(final_path))
    print(f"\n[Saved] {final_path}")

    # ── final eval on all sets ─────────────────────────
    print(f"\n{'='*70}\n  Final Evaluation\n{'='*70}")
    eval_sets = {
        "internal_val": data["val"],
        "internal_test": data["test"],
        "klue_val": data["klue_val"],
        "wikiann_val": data["wikiann_val"],
        "wikiann_test": data["wikiann_test"],
    }
    all_results = {}
    for name, samples in eval_sets.items():
        if not samples:
            continue
        ds = PIINerDataset(samples, tokenizer, args.max_length)
        metrics = trainer.evaluate(ds, metric_key_prefix=name)
        print(f"  {name:<15s}: macro_f1={metrics.get(f'{name}_macro_f1', 0):.4f} "
              f"micro_f1={metrics.get(f'{name}_micro_f1', 0):.4f} "
              f"loss={metrics.get(f'{name}_loss', 0):.4f}")
        all_results[name] = metrics

    with (output_dir / "all_eval_results.json").open("w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n[Saved] {output_dir / 'all_eval_results.json'}")


if __name__ == "__main__":
    main()
