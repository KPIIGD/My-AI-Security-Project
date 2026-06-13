"""Upload Korean PII NER v3 dataset to HuggingFace Datasets.

Usage:

    # 1. Get HF token (write scope) from https://huggingface.co/settings/tokens
    # 2. Set environment variable:
    $env:HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    # 3. Run:
    python upload_to_hf.py

The script splits the monolithic pii_ner_v3.json into per-split JSONL files
(train / val / test / klue_test), writes label_map.json + meta.json, and
uploads everything to https://huggingface.co/datasets/vmaca123/korean-pii-ner-v3

Idempotent: re-running uploads any changed files only.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi, create_repo


REPO_ID = "vmaca123/korean-pii-ner-v3"
HERE = Path(__file__).resolve().parent
NER_ROOT = HERE.parent  # c:/My-AI-Security-Project/PII/ner
SOURCE_FILE = NER_ROOT / "data" / "pii_ner_v3.json"


def _ensure_token() -> str:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        print(
            "[error] HF_TOKEN env var missing. Get a write-scope token at\n"
            "        https://huggingface.co/settings/tokens\n"
            "        and run:  $env:HF_TOKEN = \"hf_xxx...\"",
            file=sys.stderr,
        )
        sys.exit(2)
    return token


def _prepare_splits(data: dict, output_dir: Path) -> list[Path]:
    """Split monolithic JSON into per-split JSONL files."""
    produced: list[Path] = []
    for split_name in ("train", "val", "test", "klue_test"):
        if split_name not in data:
            print(f"  skip: split '{split_name}' not in source")
            continue
        path = output_dir / f"{split_name}.jsonl"
        with path.open("w", encoding="utf-8") as fp:
            for example in data[split_name]:
                fp.write(json.dumps(example, ensure_ascii=False) + "\n")
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"  wrote {path.name}: {len(data[split_name]):>6} examples ({size_mb:.1f} MB)")
        produced.append(path)
    return produced


def _write_label_map(data: dict, output_dir: Path) -> Path:
    path = output_dir / "label_map.json"
    payload = {
        "label2id": data.get("label2id", {}),
        "id2label": data.get("id2label", {}),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote {path.name}: {len(payload['label2id'])} labels")
    return path


def _write_meta(data: dict, output_dir: Path) -> Path:
    path = output_dir / "meta.json"
    payload = data.get("meta", {})
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote {path.name}")
    return path


def main() -> int:
    if not SOURCE_FILE.is_file():
        print(f"[error] source not found: {SOURCE_FILE}", file=sys.stderr)
        return 2

    token = _ensure_token()

    print(f"[1/4] Loading {SOURCE_FILE.name} ({SOURCE_FILE.stat().st_size / (1024*1024):.1f} MB)...")
    with SOURCE_FILE.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    print(f"[2/4] Writing split files to {HERE}...")
    _prepare_splits(data, HERE)
    _write_label_map(data, HERE)
    _write_meta(data, HERE)

    print(f"[3/4] Ensuring HuggingFace dataset repo '{REPO_ID}' exists...")
    create_repo(
        repo_id=REPO_ID,
        repo_type="dataset",
        exist_ok=True,
        token=token,
        private=False,
    )

    print(f"[4/4] Uploading folder {HERE} to '{REPO_ID}'...")
    api = HfApi(token=token)
    api.upload_folder(
        folder_path=str(HERE),
        repo_id=REPO_ID,
        repo_type="dataset",
        commit_message="Initial v3 dataset release (KLUE 21k + Faker 10k + composite 2k + hard_neg 1k)",
        ignore_patterns=["upload_to_hf.py", "__pycache__/*", "*.pyc"],
    )

    print(f"\nDone! View at https://huggingface.co/datasets/{REPO_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
