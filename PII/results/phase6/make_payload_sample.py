"""Build an exact-size payload sample from an existing payload JSON file."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_payloads(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and isinstance(data.get("payloads"), list):
        return dict(data.get("metadata", {})), list(data["payloads"])
    if isinstance(data, list):
        return {}, data
    raise ValueError(f"Unsupported input format: {path}")


def _bucket_key(payload: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(payload.get("lang", "")),
        str(payload.get("validity_group", "")),
        str(payload.get("pii_type", "")),
        str(payload.get("mutation_level", "")),
    )


def build_sample(
    payloads: list[dict[str, Any]],
    target: int,
    seed: int,
    with_replacement: bool,
) -> list[dict[str, Any]]:
    if target <= 0:
        raise ValueError("target must be positive")
    if target > len(payloads) and not with_replacement:
        raise ValueError("target is larger than source; pass --with-replacement")

    rng = random.Random(seed)
    buckets: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for payload in payloads:
        buckets[_bucket_key(payload)].append(payload)

    keys = list(buckets.keys())
    allocations: dict[tuple[str, str, str, str], int] = {}
    remaining = target
    source_n = len(payloads)
    for idx, key in enumerate(keys):
        if idx == len(keys) - 1:
            allocations[key] = remaining
            continue
        n = round(target * len(buckets[key]) / source_n)
        if not with_replacement:
            n = min(n, len(buckets[key]))
        allocations[key] = n
        remaining -= n

    sampled: list[dict[str, Any]] = []
    for key, n in allocations.items():
        values = list(buckets[key])
        if with_replacement:
            sampled.extend(rng.choice(values) for _ in range(n))
        else:
            rng.shuffle(values)
            sampled.extend(values[:n])

    while len(sampled) < target:
        sampled.append(rng.choice(payloads))
    if len(sampled) > target:
        sampled = sampled[:target]

    rng.shuffle(sampled)
    return [dict(payload) for payload in sampled]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an exact-size payload sample.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--target", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=20260430)
    parser.add_argument("--with-replacement", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    source_meta, payloads = _load_payloads(input_path)
    sampled = build_sample(payloads, args.target, args.seed, args.with_replacement)

    metadata = dict(source_meta)
    metadata.update(
        {
            "source_file": str(input_path),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "sample_target": args.target,
            "sample_seed": args.seed,
            "with_replacement": args.with_replacement,
            "source_count": len(payloads),
            "count": len(sampled),
        }
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump({"metadata": metadata, "payloads": sampled}, f, ensure_ascii=False)
    print(f"saved {len(sampled)} payloads to {output_path}")


if __name__ == "__main__":
    main()
