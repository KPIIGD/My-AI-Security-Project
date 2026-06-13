"""
v0.2 BaseNERDetector Protocol 구현체 — fine-tuned klue/roberta-large NER.

PIISpan contract:
  - start, end는 raw text char offset
  - span.text == raw_text[span.start:span.end] 보장
  - entity_type은 v0.2 EntityType enum
  - score [0, 1]
  - reason_codes ≥ 1
  - action = CANDIDATE (resolver/policy가 최종 결정)

NER scope: NAME → PERSON_NAME, ADDRESS → ADDRESS_FULL, ORG → ORGANIZATION

v1 known limitation:
  Conjunctive pattern (e.g. "{name}이고 {address}") 에서 NAME이 ADDRESS span에 빨려들어감.
  Postprocess heuristic: ADDRESS span 시작이 시·도 prefix 아니면 split.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer


# v0.2 EntityType 매핑 (NER label → pipeline entity)
LABEL_TO_ENTITY_TYPE = {
    "NAME": "PERSON_NAME",
    "ADDRESS": "ADDRESS_FULL",
    "ORG": "ORGANIZATION",
}

# v0.2 RiskLevel 기본 매핑
ENTITY_TO_RISK_LEVEL = {
    "PERSON_NAME": "P1",
    "ADDRESS_FULL": "P1",
    "ORGANIZATION": "P2",
}

# 한국 시·도 prefix (실 행정구역; ADDRESS span 시작 검증용)
SIDO_PREFIXES = (
    "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시",
    "대전광역시", "울산광역시", "세종특별자치시",
    "경기도", "강원특별자치도", "강원도",
    "충청북도", "충청남도", "전라북도", "전북특별자치도", "전라남도",
    "경상북도", "경상남도", "제주특별자치도",
    "서울시", "부산시", "대구시", "인천시", "광주시", "대전시", "울산시", "세종시",
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
)

# NAME 본체에서 떼낼 조사 (boundary corrector v0 — 우선순위 긴 것부터)
NAME_SUFFIX_PATTERN = re.compile(
    r"(이고|이며|하고|와는|과는|이랑|에게|한테|에서|이가|은|는|이|가|"
    r"을|를|에|와|과|랑|도|만|부터|까지|이라고|라고|이라는|라는|"
    r"님|씨|군|양)$"
)


class FinetunedKoreanNERDetector:
    """v0.2 BaseNERDetector implementation.

    Usage:
        det = FinetunedKoreanNERDetector(
            model_path="models/pii_ner_v1/final",
            calibration_path="models/pii_ner_v1/final/calibration.json",
        )
        spans = det.detect(raw_text, preprocessed, request)
    """

    detector_id = "ner.finetuned.klue-bert-v1"

    def __init__(
        self,
        model_path: str,
        calibration_path: Optional[str] = None,
        device: str = "auto",
        max_length: int = 256,
    ):
        self.model_path = Path(model_path)
        self.max_length = max_length

        # device 결정
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        # 모델/토크나이저 로드
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
        self.model = AutoModelForTokenClassification.from_pretrained(str(self.model_path))
        self.model.to(self.device)
        self.model.eval()

        # label map (id ↔ label)
        self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}

        # calibration
        self.calibration = None
        self.temperature = 1.0
        self.per_entity_threshold = {
            "PERSON_NAME": 0.85,
            "ADDRESS_FULL": 0.80,
            "ORGANIZATION": 0.75,
        }
        if calibration_path and Path(calibration_path).exists():
            with open(calibration_path, "r", encoding="utf-8") as f:
                self.calibration = json.load(f)
            self.temperature = self.calibration.get("temperature", 1.0)
            self.per_entity_threshold.update(
                self.calibration.get("per_entity_threshold", {})
            )

    # ─────────────────────────────────────────────────────
    # v0.2 BaseNERDetector interface
    # ─────────────────────────────────────────────────────

    def detect(self, raw_text, preprocessed=None, request=None) -> list:
        """Return list of candidate PIISpan-like dicts with raw-text offsets.

        v0.2 PIISpan 으로 변환은 호출자가 담당 (이 모듈은 schema 직접 import 안 함).
        반환 형식:
            [{
              "start": int, "end": int, "text": str,
              "entity_type": str, "score": float,
              "sources": ("ner",), "risk_level": str,
              "detector_ids": ("ner.finetuned.klue-bert-v1",),
              "reason_codes": (...)
            }, ...]
        """
        if not raw_text:
            return []

        # 1. char list 로 분해 (raw offset 1:1 매핑)
        chars = list(raw_text)

        # 2. 긴 문장은 sliding window
        if len(chars) > self.max_length - 2:  # -2 for [CLS]/[SEP]
            return self._sliding_window_detect(raw_text, chars)

        # 3. tokenize + forward
        spans_raw = self._infer_single_window(chars, offset=0)
        corrected = self._split_address_name_conjunction(spans_raw, raw_text)
        return self._postprocess_spans(corrected, raw_text)

    # ─────────────────────────────────────────────────────
    # 내부 helper
    # ─────────────────────────────────────────────────────

    def _infer_single_window(self, chars: list[str], offset: int) -> list[dict]:
        """char list 한 window 입력 → BIO contiguous span 리스트."""
        enc = self.tokenizer(
            chars,
            is_split_into_words=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        enc = {k: v.to(self.device) for k, v in enc.items()}
        word_ids = enc.pop("word_ids", None)  # tokenizer 출력에서 word_ids 추출용
        # word_ids는 BatchEncoding 객체에서만 가능 — 재계산
        enc_batch = self.tokenizer(
            chars,
            is_split_into_words=True,
            truncation=True,
            max_length=self.max_length,
        )
        word_ids = enc_batch.word_ids()

        with torch.no_grad():
            logits = self.model(**enc).logits[0]  # (seq_len, num_labels)
            logits = logits / self.temperature
            probs = torch.softmax(logits, dim=-1)
            pred_ids = probs.argmax(dim=-1).cpu().tolist()
            pred_probs = probs.cpu().tolist()

        # BIO → contiguous span
        spans = self._bio_to_spans(pred_ids, pred_probs, word_ids, offset=offset)
        return spans

    def _bio_to_spans(
        self,
        pred_ids: list[int],
        pred_probs: list[list[float]],
        word_ids: list[Optional[int]],
        offset: int,
    ) -> list[dict]:
        """token-level BIO → char-level span 리스트."""
        spans = []
        cur_type = None
        cur_start = None
        cur_end = None
        cur_scores = []

        for tok_idx, (wid, pid) in enumerate(zip(word_ids, pred_ids)):
            if wid is None:  # special token (CLS/SEP/PAD)
                continue
            label = self.id2label[pid]
            char_idx = wid + offset

            if label == "O":
                if cur_type is not None:
                    spans.append(self._finalize_span(
                        cur_type, cur_start, cur_end, cur_scores
                    ))
                cur_type, cur_start, cur_end, cur_scores = None, None, None, []
            elif label.startswith("B-"):
                if cur_type is not None:
                    spans.append(self._finalize_span(
                        cur_type, cur_start, cur_end, cur_scores
                    ))
                cur_type = label[2:]
                cur_start = char_idx
                cur_end = char_idx + 1
                # entity의 max prob (B-type id)
                entity_score = pred_probs[tok_idx][pid]
                cur_scores = [entity_score]
            elif label.startswith("I-"):
                if cur_type is None or cur_type != label[2:]:
                    # malformed BIO — start new span
                    if cur_type is not None:
                        spans.append(self._finalize_span(
                            cur_type, cur_start, cur_end, cur_scores
                        ))
                    cur_type = label[2:]
                    cur_start = char_idx
                    cur_end = char_idx + 1
                    cur_scores = [pred_probs[tok_idx][pid]]
                else:
                    cur_end = char_idx + 1
                    cur_scores.append(pred_probs[tok_idx][pid])

        if cur_type is not None:
            spans.append(self._finalize_span(cur_type, cur_start, cur_end, cur_scores))

        return spans

    def _finalize_span(self, ner_type, start, end, scores) -> dict:
        score = float(sum(scores) / len(scores)) if scores else 0.0
        return {
            "ner_type": ner_type,
            "start": start,
            "end": end,
            "score": score,
        }

    def _sliding_window_detect(self, raw_text: str, chars: list[str]) -> list[dict]:
        """긴 입력 → window 분할 + IoU merge."""
        stride = self.max_length // 2
        window_size = self.max_length - 2
        all_spans = []
        for start in range(0, len(chars), stride):
            end = min(start + window_size, len(chars))
            window_chars = chars[start:end]
            spans_raw = self._infer_single_window(window_chars, offset=start)
            all_spans.extend(spans_raw)
            if end == len(chars):
                break

        # overlap merge: same ner_type + IoU >= 0.5 → mean score
        merged = self._merge_overlapping(all_spans, iou_threshold=0.5)
        corrected = self._split_address_name_conjunction(merged, raw_text)
        return self._postprocess_spans(corrected, raw_text)

    def _merge_overlapping(self, spans: list[dict], iou_threshold: float = 0.5) -> list[dict]:
        if not spans:
            return []
        spans = sorted(spans, key=lambda s: (s["start"], s["end"]))
        merged: list[dict] = []
        for s in spans:
            if not merged:
                merged.append(s)
                continue
            last = merged[-1]
            if last["ner_type"] == s["ner_type"]:
                overlap_start = max(last["start"], s["start"])
                overlap_end = min(last["end"], s["end"])
                if overlap_end > overlap_start:
                    union = max(last["end"], s["end"]) - min(last["start"], s["start"])
                    iou = (overlap_end - overlap_start) / union
                    if iou >= iou_threshold:
                        # merge
                        last["start"] = min(last["start"], s["start"])
                        last["end"] = max(last["end"], s["end"])
                        last["score"] = (last["score"] + s["score"]) / 2
                        continue
            merged.append(s)
        return merged

    def _split_address_name_conjunction(
        self, spans: list[dict], raw_text: str
    ) -> list[dict]:
        """v1 모델 한계 보정: ADDRESS span 시작이 시·도 prefix 가 아니면 NAME으로 split.

        예: ADDRESS span '홍길동이고 서울시 강남구 ...' →
            NAME 'X' (조사·이고 stripped) + ADDRESS '서울시 강남구 ...'

        시·도 prefix 안에 있으면 그대로 두고, 없으면 keep.
        score 가 calibrated 라 split 후도 mean 그대로 유지.
        """
        result = []
        for s in spans:
            if s["ner_type"] != "ADDRESS":
                result.append(s)
                continue
            span_text = raw_text[s["start"]:s["end"]]
            # 시작이 이미 시·도 prefix이면 OK
            if any(span_text.startswith(p) for p in SIDO_PREFIXES):
                result.append(s)
                continue
            # 시·도 prefix가 span 내부에 있나?
            cut_pos = -1
            for p in SIDO_PREFIXES:
                idx = span_text.find(p)
                if idx > 0 and (cut_pos == -1 or idx < cut_pos):
                    cut_pos = idx
            if cut_pos < 0:
                # 시·도 못 찾음 → ADDRESS 신뢰성 낮음. 일단 그대로 keep (downstream에서 처리)
                result.append(s)
                continue
            # split: [0:cut_pos] = NAME 후보, [cut_pos:] = ADDRESS
            name_text = span_text[:cut_pos].rstrip()
            # 조사 strip
            m = NAME_SUFFIX_PATTERN.search(name_text)
            if m:
                name_text = name_text[:m.start()]
            name_text = name_text.strip()
            # NAME 본체가 2-10 char (한국어 이름 일반 범위) 일 때만 NAME으로 emit
            if 2 <= len(name_text) <= 10:
                name_start = s["start"]
                name_end = name_start + len(name_text)
                result.append({
                    "ner_type": "NAME",
                    "start": name_start,
                    "end": name_end,
                    "score": s["score"] * 0.9,  # heuristic 보정이므로 score 약간 감점
                    "_heuristic_split": True,
                })
            # ADDRESS 본체
            addr_start = s["start"] + cut_pos
            result.append({
                "ner_type": "ADDRESS",
                "start": addr_start,
                "end": s["end"],
                "score": s["score"],
                "_heuristic_split": True,
            })
        return result

    def _postprocess_spans(self, raw_spans: list[dict], raw_text: str) -> list[dict]:
        """raw NER spans → v0.2 호환 candidate 리스트 (threshold + entity 매핑)."""
        results = []
        for s in raw_spans:
            ner_type = s["ner_type"]
            entity_type = LABEL_TO_ENTITY_TYPE.get(ner_type)
            if entity_type is None:
                continue

            threshold = self.per_entity_threshold.get(entity_type, 0.75)
            if s["score"] < threshold:
                continue

            start, end = s["start"], s["end"]
            text = raw_text[start:end]

            reason_codes = [
                "ner.argmax",
                "ner.softmax_mean",
                f"ner.length_{end - start}",
            ]
            if s.get("_heuristic_split"):
                reason_codes.append("ner.heuristic_split_v1")

            results.append({
                "start": start,
                "end": end,
                "text": text,
                "entity_type": entity_type,
                "score": s["score"],
                "sources": ("ner",),
                "risk_level": ENTITY_TO_RISK_LEVEL.get(entity_type, "P2"),
                "detector_ids": (self.detector_id,),
                "reason_codes": tuple(reason_codes),
            })
        return results


# ─────────────────────────────────────────────────────
# CLI 테스트용 entrypoint
# ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, sys
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, help="model dir")
    p.add_argument("--calibration", default=None)
    p.add_argument("--text", default="홍길동이 서울시 강남구 테헤란로 152에 거주합니다. 삼성전자 소속.")
    args = p.parse_args()

    det = FinetunedKoreanNERDetector(args.model, args.calibration)
    spans = det.detect(args.text)
    print(f"input: {args.text}")
    print(f"spans ({len(spans)}):")
    for s in spans:
        print(f"  [{s['entity_type']:<15s}] {s['start']:>3d}:{s['end']:<3d} "
              f"score={s['score']:.3f} text={s['text']!r}")
