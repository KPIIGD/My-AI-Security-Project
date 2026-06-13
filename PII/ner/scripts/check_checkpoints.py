"""
W1 Day 3 작업 — A-primary 후보 체크포인트 sanity check.

3개 후보 모델 로드 후:
- id2label 출력 (라벨 스키마 차이 확인)
- 200문장 샘플 추론으로 출력 형태 확인
- 라이선스 메타 정보 출력
- macro-F1 측정 결과는 별도 스크립트 (eval_checkpoints.py)에서

사용:
  python check_checkpoints.py
  python check_checkpoints.py --model monologg
"""
import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForTokenClassification


# A-primary 후보 (라이선스 직접 확인 필수)
CANDIDATES = {
    "monologg": {
        "ckpt": "monologg/koelectra-base-v3-naver-ner",
        "license_note": "Naver NLP Challenge 2018 데이터 = CC-BY-NC-SA 4.0 (비영리). "
                        "캡스톤 발표 OK (§96 면책), GitHub 공개 ❌, 포트폴리오 ⚠️",
        "expected_labels": "PS_/LC_/OG_/DT_/TI_/QT_ 계열",
    },
    "kpf": {
        "ckpt": "KPF/KPF-bert-ner",
        "license_note": "한국언론진흥재단 뉴스 NER. 모델 카드 직접 확인 필요. "
                        "공공 기관 데이터로 일반적으로 자유로움 추정",
        "expected_labels": "PER/LOC/ORG/MISC 또는 confused",
    },
    "leo97": {
        "ckpt": "Leo97/KoELECTRA-small-v3-modu-ner",
        "license_note": "국립국어원 모두의 말뭉치. 연구·교육 OK, 재배포 제약 있음",
        "expected_labels": "modu-ner 스키마 (PS/LC/OG/DT/TI/QT 등)",
    },
    # Fallback 후보 (모든 라이선스 회색이면 자체 학습)
    "klue_bert": {
        "ckpt": "klue/bert-base",
        "license_note": "★ MLM-only, NER head 랜덤. 단독 추론 불가. C-fallback 학습용 base",
        "expected_labels": "(NER head 없음)",
    },
}

# Sanity check 샘플 문장 (한국어 PII 다양성 커버)
SANITY_SAMPLES = [
    "안녕하세요, 홍길동입니다. 010-1234-5678로 연락주세요.",
    "삼성전자 인사팀 김과장에게 보고드립니다.",
    "서울특별시 강남구 테헤란로 152 101동 1203호로 배송 부탁드려요.",
    "환자 김민수님은 페니실린 알레르기가 있습니다.",
    "(주)카카오 박사장님 이메일은 ceo@kakao.com입니다.",
    "고려대학교 컴퓨터공학과 이지영 교수 연락처입니다.",
]


def check_one(name: str) -> dict:
    """체크포인트 1개 sanity check."""
    info = CANDIDATES[name]
    ckpt = info["ckpt"]
    print(f"\n{'='*70}")
    print(f"  [{name.upper()}] {ckpt}")
    print(f"{'='*70}")
    print(f"  License: {info['license_note']}")
    print(f"  Expected labels: {info['expected_labels']}")

    result = {
        "name": name,
        "ckpt": ckpt,
        "license_note": info["license_note"],
        "loaded": False,
        "id2label": None,
        "num_labels": None,
        "samples": [],
        "error": None,
    }

    try:
        tokenizer = AutoTokenizer.from_pretrained(ckpt)
        model = AutoModelForTokenClassification.from_pretrained(ckpt)
        model.eval()
        result["loaded"] = True
        result["id2label"] = dict(model.config.id2label)
        result["num_labels"] = len(result["id2label"])

        print(f"\n  ✅ Loaded. num_labels={result['num_labels']}")
        print(f"  id2label: {result['id2label']}")

        # NER head 검증 (랜덤 초기화 경고 체크)
        if result["num_labels"] <= 2 or all(
            v in {"LABEL_0", "LABEL_1"} or v.startswith("LABEL_")
            for v in result["id2label"].values()
        ):
            print(f"  ⚠️  NER head가 랜덤 초기화 가능성. 단독 추론 불가.")

        # 샘플 추론
        print(f"\n  --- 샘플 추론 (3개) ---")
        import torch
        for i, sent in enumerate(SANITY_SAMPLES[:3]):
            inputs = tokenizer(sent, return_tensors="pt", return_offsets_mapping=True)
            offsets = inputs.pop("offset_mapping")[0].tolist()
            with torch.no_grad():
                logits = model(**inputs).logits
            preds = logits.argmax(-1)[0].tolist()
            tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
            spans = []
            for tok, label_id, (s, e) in zip(tokens, preds, offsets):
                if s == e:  # special tokens
                    continue
                label = result["id2label"][label_id]
                if label != "O" and not label.startswith("LABEL_"):
                    spans.append({"token": tok, "label": label, "char": (s, e)})
            print(f"  [{i+1}] {sent[:60]}...")
            for sp in spans[:5]:
                print(f"      {sp['label']:<12} '{sp['token']}' @ {sp['char']}")
            result["samples"].append({"sentence": sent, "spans": spans})

    except Exception as e:
        result["error"] = str(e)
        print(f"  ❌ Failed: {e}")

    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=list(CANDIDATES.keys()) + ["all"], default="all")
    p.add_argument("--out", default="../reports/checkpoint_report.json")
    args = p.parse_args()

    results = []
    if args.model == "all":
        for name in CANDIDATES:
            results.append(check_one(name))
    else:
        results.append(check_one(args.model))

    out_path = Path(__file__).parent / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📁 Saved: {out_path.resolve()}")


if __name__ == "__main__":
    main()
