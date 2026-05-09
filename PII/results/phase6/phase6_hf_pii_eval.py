"""Evaluate Hugging Face Korean PII NER models on project payloads."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelSpec:
    name: str
    repo_id: str
    framework: str | None = None
    revision: str | None = None
    subfolder: str | None = None
    runner: str = "transformers"


MODEL_SPECS = [
    ModelSpec("mncai", "mncai/Korean-PII-Masking-Model", subfolder="bert"),
    ModelSpec(
        "alphagyuu",
        "alphagyuu/Korean-PII-Masking-BertForTokenClassification",
        framework="tf",
    ),
    ModelSpec("piilot", "ParkJunSeong/PIILOT_NER_Model"),
    ModelSpec("seungkukim", "seungkukim/korean-pii-masking"),
    ModelSpec("aegis", "YATAV-ENT/aegis-personal-pii-ner", revision="v2", runner="onnx"),
]

TRUE = "TRUE"
BYPASS = "BYPASS"
ERROR = "ERROR"
NON_ENTITY_LABELS = {"", "O", "LABEL_0"}


def _load_payloads(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and isinstance(data.get("payloads"), list):
        return list(data["payloads"])
    if isinstance(data, list):
        return data
    raise ValueError(f"Unsupported input format: {path}")


def _digits(text: str) -> str:
    return re.sub(r"\D", "", text or "")


def _normalize_text(text: str) -> str:
    fullwidth_map = {chr(0xFF10 + i): str(i) for i in range(10)}
    return "".join(fullwidth_map.get(ch, ch) for ch in text or "").lower()


def _target_candidates(payload: dict[str, Any]) -> list[str]:
    keys = [
        "original",
        "pii_value",
        "original_name",
        "mutated_name",
        "original_address",
        "mutated_address",
        "account",
        "bank_account",
        "card",
        "email",
        "phone",
        "rrn",
    ]
    values: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    if not values and payload.get("original"):
        values.append(str(payload["original"]))
    seen = set()
    deduped = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


_KOREAN_NORMALIZER = None


def _get_korean_normalizer():
    global _KOREAN_NORMALIZER
    if _KOREAN_NORMALIZER is not None:
        return _KOREAN_NORMALIZER
    root = Path(__file__).resolve().parents[3]
    layer0_path = root / "PII" / "layer_0"
    if str(layer0_path) not in sys.path:
        sys.path.insert(0, str(layer0_path))
    from korean_normalizer import KoreanNormalizer

    _KOREAN_NORMALIZER = KoreanNormalizer()
    return _KOREAN_NORMALIZER


def preprocess_text(text: str, mode: str) -> str:
    if mode == "none":
        return text
    if mode == "korean":
        return _get_korean_normalizer().normalize(text)
    raise ValueError(f"Unsupported preprocess mode: {mode}")


def _span_overlaps_target(text: str, entity: dict[str, Any], candidates: list[str]) -> bool:
    start = entity.get("start")
    end = entity.get("end")
    if isinstance(start, int) and isinstance(end, int) and start < end:
        for candidate in candidates:
            idx = text.find(candidate)
            if idx >= 0 and max(start, idx) < min(end, idx + len(candidate)):
                return True
    return False


def _entity_hits_target(text: str, entity: dict[str, Any], candidates: list[str]) -> bool:
    entity_text = str(entity.get("word") or entity.get("text") or "")
    entity_norm = _normalize_text(entity_text)
    text_norm = _normalize_text(text)

    for candidate in candidates:
        cand_norm = _normalize_text(candidate)
        if cand_norm and (cand_norm in entity_norm or entity_norm in cand_norm):
            return True

        cand_digits = _digits(candidate)
        ent_digits = _digits(entity_text)
        if len(cand_digits) >= 4 and ent_digits:
            if cand_digits in ent_digits or ent_digits in cand_digits:
                return True

        if cand_norm and cand_norm in text_norm and _span_overlaps_target(text, entity, [candidate]):
            return True

    return False


def _evaluate_entities(
    payload: dict[str, Any], entities: list[dict[str, Any]], evaluated_text: str
) -> tuple[str, bool, int, list[str]]:
    entities = [entity for entity in entities if not _is_non_entity(entity)]
    if not entities:
        return BYPASS, False, 0, []

    candidates = _target_candidates(payload)
    labels = [
        str(e.get("entity_group") or e.get("entity") or e.get("label") or "")
        for e in entities
    ]
    target_hit = any(_entity_hits_target(evaluated_text, entity, candidates) for entity in entities)
    return (TRUE if target_hit else BYPASS), target_hit, len(entities), sorted(set(labels))


def _is_non_entity(entity: dict[str, Any]) -> bool:
    label = str(entity.get("entity_group") or entity.get("entity") or entity.get("label") or "")
    return label in NON_ENTITY_LABELS


def _safe_entity(entity: dict[str, Any]) -> dict[str, Any]:
    def maybe_int(value: Any) -> int | None:
        if value is None:
            return None
        return int(value)

    return {
        "entity": entity.get("entity"),
        "entity_group": entity.get("entity_group"),
        "word": entity.get("word"),
        "score": float(entity.get("score", 0.0)) if entity.get("score") is not None else None,
        "start": maybe_int(entity.get("start")),
        "end": maybe_int(entity.get("end")),
    }


def _stats(cases: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(cases)
    if not n:
        return {
            "n": 0,
            "any_detection_rate": 0.0,
            "target_hit_rate": 0.0,
            "target_bypass_rate": 0.0,
            "error_rate": 0.0,
        }
    any_detected = sum(1 for c in cases if c.get("entity_count", 0) > 0)
    target_hit = sum(1 for c in cases if c.get("target_hit"))
    errors = sum(1 for c in cases if c.get("classification") == ERROR)
    return {
        "n": n,
        "any_detected": any_detected,
        "target_hit": target_hit,
        "errors": errors,
        "any_detection_rate": round(100 * any_detected / n, 2),
        "target_hit_rate": round(100 * target_hit / n, 2),
        "target_bypass_rate": round(100 * (n - target_hit) / n, 2),
        "error_rate": round(100 * errors / n, 2),
    }


def _slice_by(cases: list[dict[str, Any]], key: str) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        buckets[str(case.get(key, ""))].append(case)
    return {k: _stats(v) for k, v in sorted(buckets.items(), key=lambda kv: kv[0])}


def _latency_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    values = sorted(int(c.get("latency_ms", 0)) for c in cases if not c.get("error"))
    if not values:
        return {"avg_ms": 0, "p50_ms": 0, "p95_ms": 0, "max_ms": 0}

    def q(frac: float) -> int:
        idx = int(round((len(values) - 1) * frac))
        return values[max(0, min(idx, len(values) - 1))]

    return {
        "avg_ms": int(round(sum(values) / len(values))),
        "p50_ms": q(0.50),
        "p95_ms": q(0.95),
        "max_ms": values[-1],
    }


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        by_model[str(result.get("model", ""))].append(result)

    summary: dict[str, Any] = {}
    for model_name, cases in sorted(by_model.items()):
        summary[model_name] = {
            "overall": _stats(cases),
            "by_lang": _slice_by(cases, "lang"),
            "by_validity": _slice_by(cases, "validity_group"),
            "by_mutation_level": _slice_by(cases, "mutation_level"),
            "by_pii_type": _slice_by(cases, "pii_type"),
            "latency": _latency_summary(cases),
        }
    return summary


def _save_output(
    output_path: Path,
    input_path: Path,
    results: list[dict[str, Any]],
    started: float,
    args: argparse.Namespace,
) -> None:
    output = {
        "metadata": {
            "run": "phase6_hf_pii_eval",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "input_file": str(input_path),
            "elapsed_sec": round(time.time() - started, 2),
            "device": args.device,
            "batch_size": args.batch_size,
            "preprocess": args.preprocess,
            "models": [spec.repo_id for spec in _select_models(args.models)],
            "result_count": len(results),
        },
        "summary": build_summary(results),
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def _select_models(model_arg: str) -> list[ModelSpec]:
    if not model_arg or model_arg == "all":
        return MODEL_SPECS
    wanted = {part.strip() for part in model_arg.split(",") if part.strip()}
    selected = [
        spec
        for spec in MODEL_SPECS
        if spec.name in wanted or spec.repo_id in wanted
    ]
    missing = wanted - {spec.name for spec in selected} - {spec.repo_id for spec in selected}
    if missing:
        raise ValueError(f"Unknown model selector(s): {', '.join(sorted(missing))}")
    return selected


def _load_pipeline(spec: ModelSpec, args: argparse.Namespace):
    if spec.runner == "onnx":
        return OnnxTokenClassificationPipeline(spec, args)

    try:
        from transformers import pipeline
    except Exception as exc:
        raise RuntimeError(
            "transformers is not installed. Run: pip install -r requirements-hf.txt"
        ) from exc

    if spec.subfolder:
        from transformers import BertConfig, BertForTokenClassification, BertTokenizerFast

        config = BertConfig.from_pretrained(spec.repo_id, subfolder=spec.subfolder)
        model = BertForTokenClassification.from_pretrained(
            spec.repo_id,
            subfolder=spec.subfolder,
            config=config,
        )
        tokenizer = BertTokenizerFast.from_pretrained(spec.repo_id, subfolder=spec.subfolder)
        return pipeline(
            task="token-classification",
            model=model,
            tokenizer=tokenizer,
            aggregation_strategy=args.aggregation_strategy,
            device=-1 if args.device == "cpu" else 0,
        )

    if spec.framework == "tf":
        from transformers import AutoTokenizer, TFAutoModelForTokenClassification

        tokenizer = AutoTokenizer.from_pretrained(spec.repo_id)
        model = TFAutoModelForTokenClassification.from_pretrained(spec.repo_id)
        return pipeline(
            task="token-classification",
            model=model,
            tokenizer=tokenizer,
            aggregation_strategy=args.aggregation_strategy,
            framework="tf",
        )

    device = -1 if args.device == "cpu" else 0
    kwargs: dict[str, Any] = {
        "task": "token-classification",
        "model": spec.repo_id,
        "tokenizer": spec.repo_id,
        "aggregation_strategy": args.aggregation_strategy,
        "device": device,
    }
    if spec.revision:
        kwargs["revision"] = spec.revision
    if spec.framework:
        kwargs["framework"] = spec.framework
    if spec.subfolder:
        kwargs["subfolder"] = spec.subfolder
    return pipeline(**kwargs)


class OnnxTokenClassificationPipeline:
    def __init__(self, spec: ModelSpec, args: argparse.Namespace):
        try:
            import numpy as np
            import onnxruntime as ort
            from huggingface_hub import hf_hub_download
            from transformers import AutoTokenizer
        except Exception as exc:
            raise RuntimeError(
                "ONNX model support requires onnxruntime. Run: pip install -r requirements-hf.txt"
            ) from exc

        self.np = np
        def download_cached(filename: str) -> str:
            try:
                return hf_hub_download(spec.repo_id, filename, revision=spec.revision)
            except Exception:
                return hf_hub_download(
                    spec.repo_id,
                    filename,
                    revision=spec.revision,
                    local_files_only=True,
                )

        model_path = download_cached("onnx/model_quantized.onnx")
        label_map_path = download_cached("label_map.json")
        with open(label_map_path, "r", encoding="utf-8") as f:
            label_map = json.load(f)
        self.id2label = {int(k): v for k, v in label_map["id2label"].items()}
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(spec.repo_id, revision=spec.revision)
        except Exception:
            self.tokenizer = AutoTokenizer.from_pretrained(
                spec.repo_id,
                revision=spec.revision,
                local_files_only=True,
            )
        providers = ["CPUExecutionProvider"]
        self.session = ort.InferenceSession(model_path, providers=providers)
        self.input_names = {inp.name for inp in self.session.get_inputs()}

    def __call__(self, texts: list[str], batch_size: int = 16):
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_offsets_mapping=True,
            return_tensors="np",
        )
        offsets = encoded.pop("offset_mapping")
        ort_inputs = {
            key: value.astype(self.np.int64)
            for key, value in encoded.items()
            if key in self.input_names
        }
        logits = self.session.run(None, ort_inputs)[0]
        pred_ids = logits.argmax(axis=-1)
        outputs = []
        for text_idx, text in enumerate(texts):
            outputs.append(self._decode_one(text, pred_ids[text_idx], offsets[text_idx]))
        return outputs

    def _decode_one(self, text: str, pred_ids, offsets) -> list[dict[str, Any]]:
        entities: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for label_id, offset in zip(pred_ids, offsets):
            start, end = int(offset[0]), int(offset[1])
            if start == end:
                continue
            label = self.id2label.get(int(label_id), "O")
            if label == "O":
                if current:
                    entities.append(current)
                    current = None
                continue
            prefix, _, raw_type = label.partition("-")
            ent_type = raw_type or label
            if current and prefix == "I" and current["entity_group"] == ent_type and start <= current["end"] + 1:
                current["end"] = end
                current["word"] = text[current["start"] : end]
            else:
                if current:
                    entities.append(current)
                current = {
                    "entity_group": ent_type,
                    "entity": label,
                    "word": text[start:end],
                    "score": None,
                    "start": start,
                    "end": end,
                }
        if current:
            entities.append(current)
        return entities


def _load_existing(path: Path) -> tuple[list[dict[str, Any]], set[tuple[str, str]]]:
    if not path.exists():
        return [], set()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    results = list(data.get("results", []))
    done = {(str(r.get("model")), str(r.get("id"))) for r in results}
    return results, done


def _batch(items: list[dict[str, Any]], batch_size: int):
    for idx in range(0, len(items), batch_size):
        yield items[idx : idx + batch_size]


def evaluate_model(
    spec: ModelSpec,
    payloads: list[dict[str, Any]],
    done: set[tuple[str, str]],
    results: list[dict[str, Any]],
    args: argparse.Namespace,
    output_path: Path,
    input_path: Path,
    started: float,
) -> None:
    print(f"[phase6] loading {spec.name}: {spec.repo_id}")
    try:
        ner = _load_pipeline(spec, args)
    except Exception as exc:
        message = str(exc)[:500]
        print(f"[phase6] load failed for {spec.name}: {message}", file=sys.stderr)
        for payload in payloads:
            key = (spec.name, str(payload.get("id", "")))
            if key in done:
                continue
            results.append(_error_result(spec, payload, f"LOAD_ERROR: {message}"))
            done.add(key)
        _save_output(output_path, input_path, results, started, args)
        return

    pending = [
        payload for payload in payloads if (spec.name, str(payload.get("id", ""))) not in done
    ]
    total = len(pending)
    print(f"[phase6] evaluating {spec.name}: {total} pending")
    processed = 0

    for group in _batch(pending, args.batch_size):
        source_texts = [str(p.get("mutated") or p.get("text") or "") for p in group]
        texts = [preprocess_text(text, args.preprocess) for text in source_texts]
        batch_start = time.perf_counter()
        try:
            batch_entities = ner(texts, batch_size=args.batch_size)
            error = None
        except Exception as exc:
            batch_entities = [[] for _ in group]
            error = str(exc)[:500]
        batch_latency = int((time.perf_counter() - batch_start) * 1000)
        per_item_latency = int(round(batch_latency / max(1, len(group))))

        for payload, source_text, evaluated_text, entities in zip(group, source_texts, texts, batch_entities):
            if entities is None:
                entities = []
            if isinstance(entities, dict):
                entities = [entities]
            if error:
                row = _error_result(spec, payload, error, latency_ms=per_item_latency)
            else:
                classification, target_hit, entity_count, labels = _evaluate_entities(
                    payload, list(entities), evaluated_text
                )
                row = {
                    "model": spec.name,
                    "repo_id": spec.repo_id,
                    "id": payload.get("id", ""),
                    "pii_type": payload.get("pii_type", ""),
                    "original": payload.get("original", ""),
                    "mutated": source_text,
                    "evaluated_text": evaluated_text,
                    "preprocess": args.preprocess,
                    "lang": payload.get("lang", ""),
                    "validity_group": payload.get("validity_group", ""),
                    "mutation_level": payload.get("mutation_level", ""),
                    "mutation_name": payload.get("mutation_name", ""),
                    "classification": classification,
                    "target_hit": target_hit,
                    "entity_count": entity_count,
                    "labels": labels,
                    "latency_ms": per_item_latency,
                    "error": None,
                }
                if args.store_entities:
                    row["entities"] = [_safe_entity(e) for e in list(entities)]
                else:
                    row["entities_sample"] = [_safe_entity(e) for e in list(entities)[:3]]
            results.append(row)
            done.add((spec.name, str(payload.get("id", ""))))

        processed += len(group)
        if args.log_every > 0 and (processed % args.log_every == 0 or processed == total):
            print(f"[phase6] {spec.name}: {processed}/{total}")
        if args.save_every > 0 and len(results) % args.save_every < args.batch_size:
            _save_output(output_path, input_path, results, started, args)

    _save_output(output_path, input_path, results, started, args)


def _error_result(
    spec: ModelSpec,
    payload: dict[str, Any],
    error: str,
    latency_ms: int = 0,
) -> dict[str, Any]:
    return {
        "model": spec.name,
        "repo_id": spec.repo_id,
        "id": payload.get("id", ""),
        "pii_type": payload.get("pii_type", ""),
        "original": payload.get("original", ""),
        "mutated": str(payload.get("mutated") or payload.get("text") or ""),
        "evaluated_text": preprocess_text(str(payload.get("mutated") or payload.get("text") or ""), "none"),
        "preprocess": "none",
        "lang": payload.get("lang", ""),
        "validity_group": payload.get("validity_group", ""),
        "mutation_level": payload.get("mutation_level", ""),
        "mutation_name": payload.get("mutation_name", ""),
        "classification": ERROR,
        "target_hit": False,
        "entity_count": 0,
        "labels": [],
        "latency_ms": latency_ms,
        "error": error,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Hugging Face PII NER models.")
    parser.add_argument("--input", required=True, help="Input payload JSON")
    parser.add_argument("--output", required=True, help="Output result JSON")
    parser.add_argument("--models", default="all", help="all or comma-separated names/repo IDs")
    parser.add_argument("--limit", type=int, default=0, help="Evaluate first N payloads")
    parser.add_argument("--resume", default=None, help="Resume from previous output JSON")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--aggregation-strategy", default="simple")
    parser.add_argument("--log-every", type=int, default=100)
    parser.add_argument("--save-every", type=int, default=500)
    parser.add_argument("--store-entities", action="store_true")
    parser.add_argument("--preprocess", choices=("none", "korean"), default="none")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    payloads = _load_payloads(input_path)
    if args.limit > 0:
        payloads = payloads[: args.limit]

    selected = _select_models(args.models)
    results, done = _load_existing(Path(args.resume).expanduser().resolve()) if args.resume else ([], set())

    started = time.time()
    print(
        f"[phase6] input={input_path} payloads={len(payloads)} "
        f"models={','.join(spec.name for spec in selected)} device={args.device}"
    )

    for spec in selected:
        evaluate_model(spec, payloads, done, results, args, output_path, input_path, started)

    summary = build_summary(results)
    print("[phase6] done")
    for model_name, model_summary in summary.items():
        overall = model_summary["overall"]
        print(
            f"  {model_name}: target_hit={overall['target_hit_rate']}% "
            f"any_detection={overall['any_detection_rate']}% "
            f"errors={overall['errors']}"
        )


if __name__ == "__main__":
    main()
