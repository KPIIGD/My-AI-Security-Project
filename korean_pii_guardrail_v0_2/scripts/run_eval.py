#!/usr/bin/env python3
"""Evaluation runner placeholder for v0.2.

Implement after pipeline integration. This file exists to reserve the CLI contract.
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raise SystemExit(
        f"run_eval is not implemented yet. config_dir={args.config_dir} dataset={args.dataset} output={args.output}"
    )


if __name__ == "__main__":
    main()
