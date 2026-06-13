"""
W2 평가 v3 — Leo97 + ADDRESS v2 후처리 + ORG 사전 보강.

v1: baseline (Leo97 raw)               → 0.634
v2: + addr_merge (단순 max_gap)        → 0.658
v3 (이 스크립트):
  + addr_merge_v2 (행정구역 hierarchy + 도로명·번지·동호수 확장)
  + org_dict_boost (한국 주요 회사·대학·병원·기관 사전)

목표: macro-F1 ≥ 0.75
"""
from __future__ import annotations
import re
import sys
import json
from pathlib import Path
from collections import defaultdict

# 프로젝트 루트의 address_postprocess.py 임포트 가능하게
sys.path.insert(0, str(Path(__file__).parent.parent))
from address_postprocess import merge_address_spans_v2

import torch
from transformers import pipeline
from datasets import load_dataset


CKPT = "Leo97/KoELECTRA-small-v3-modu-ner"
MAX_SAMPLES = 200

ENTITY_TO_PII = {"PS": "NAME", "LC": "ADDRESS", "OG": "ORG"}


# ─────────────────────────────────────────────────────────
# ORG 사전 (한국 주요 조직명)
# ─────────────────────────────────────────────────────────
ORG_DICT = {
    # 대기업
    "삼성전자", "삼성SDI", "삼성디스플레이", "LG전자", "LG화학", "LG디스플레이",
    "SK하이닉스", "SK이노베이션", "SK텔레콤", "현대자동차", "기아", "현대모비스",
    "포스코", "포스코홀딩스", "한화솔루션", "한화에어로스페이스", "두산에너빌리티",
    "GS리테일", "GS칼텍스", "롯데케미칼", "롯데쇼핑", "신세계", "이마트",
    # IT
    "네이버", "카카오", "쿠팡", "배달의민족", "토스", "당근마켓", "야놀자",
    "엔씨소프트", "넥슨", "넷마블", "크래프톤",
    # 금융
    "신한은행", "국민은행", "우리은행", "하나은행", "농협은행", "기업은행",
    "삼성생명", "한화생명", "교보생명", "삼성화재", "현대해상", "DB손해보험",
    "신한카드", "삼성카드", "현대카드", "KB국민카드",
    # 통신
    "KT", "SKT", "LG U+",
    # 대학교
    "서울대학교", "연세대학교", "고려대학교", "성균관대학교", "한양대학교",
    "중앙대학교", "경희대학교", "건국대학교", "동국대학교", "홍익대학교",
    "이화여자대학교", "숙명여자대학교", "서강대학교", "한국외국어대학교",
    "부산대학교", "경북대학교", "전남대학교", "충남대학교", "충북대학교",
    "포항공과대학교", "카이스트", "KAIST", "지스트", "GIST", "유니스트", "UNIST",
    # 병원
    "서울대병원", "서울대학교병원", "세브란스병원", "삼성서울병원", "아산병원",
    "서울아산병원", "서울성모병원", "분당서울대학교병원", "강남세브란스병원",
    "충남대병원", "경북대병원", "전남대병원", "부산대병원",
    # 정부·공공
    "국세청", "관세청", "검찰청", "경찰청", "한국전력공사", "한국도로공사",
    "한국토지주택공사", "LH", "건강보험공단", "국민연금공단", "근로복지공단",
}

# Suffix 패턴 (사전에 없어도 매칭 가능)
ORG_SUFFIX_PATTERN = re.compile(
    r"[가-힣A-Za-z0-9]+"
    r"(?:전자|화학|중공업|건설|증권|투자증권|자산운용|은행|생명|화재|손해보험|"
    r"카드|페이|텔레콤|통신|디스플레이|모비스|반도체|"
    r"대학교|대학원|대학|학교|"
    r"병원|의료원|의원|"
    r"공사|공단|진흥원|연구원|연구소|"
    r"협회|학회|위원회|재단|"
    r"\(주\)|주식회사)"
)


def find_org_dict_spans(sentence: str) -> list[tuple]:
    """사전 + suffix 패턴으로 ORG 후보 추출."""
    spans = []
    # 1. 사전 매칭 (긴 것 우선)
    for org in sorted(ORG_DICT, key=len, reverse=True):
        for m in re.finditer(re.escape(org), sentence):
            spans.append((m.start(), m.end(), "ORG"))
    # 2. Suffix 패턴
    for m in ORG_SUFFIX_PATTERN.finditer(sentence):
        spans.append((m.start(), m.end(), "ORG"))

    # 중복 제거 + 겹침 처리 (긴 span 우선)
    spans = sorted(set(spans), key=lambda s: (-len(sentence[s[0]:s[1]]), s[0]))
    final = []
    used = [False] * len(sentence)
    for s, e, t in spans:
        if not any(used[s:e]):
            final.append((s, e, t))
            for i in range(s, e):
                used[i] = True
    return final


def merge_with_dict(ner_spans: list[tuple], dict_spans: list[tuple],
                    sentence: str) -> list[tuple]:
    """NER 결과 + 사전 결과 병합. NER가 가진 span은 유지, 빠진 ORG만 사전 추가."""
    merged = list(ner_spans)
    used_ranges = [(s, e) for s, e, t in ner_spans]
    for s, e, t in dict_spans:
        # NER가 이미 이 영역 cover?
        if any(not (e <= us or s >= ue) for us, ue in used_ranges):
            # 겹치면 skip (NER 결과 우선)
            continue
        merged.append((s, e, t))
        used_ranges.append((s, e))
    return merged


# ─────────────────────────────────────────────────────────
# 평가 helpers (기존과 동일)
# ─────────────────────────────────────────────────────────

def map_pred(entity_group: str) -> str | None:
    return ENTITY_TO_PII.get(entity_group)


def build_gold_spans(sample, label_names) -> set[tuple]:
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


def predict_spans(nlp, sentence: str) -> list[tuple]:
    pred = nlp(sentence)
    return [(int(e["start"]), int(e["end"]), map_pred(e["entity_group"]))
            for e in pred if map_pred(e["entity_group"]) is not None]


def compute_metrics(pred_list, gold_list, classes=("NAME", "ADDRESS", "ORG")):
    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    for ps, gs in zip(pred_list, gold_list):
        ps_set, gs_set = set(ps), set(gs)
        for sp in ps_set & gs_set: tp[sp[2]] += 1
        for sp in ps_set - gs_set: fp[sp[2]] += 1
        for sp in gs_set - ps_set: fn[sp[2]] += 1
    out = {}
    macro = 0.0
    for c in classes:
        p = tp[c] / (tp[c] + fp[c]) if tp[c] + fp[c] > 0 else 0.0
        r = tp[c] / (tp[c] + fn[c]) if tp[c] + fn[c] > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        out[c] = {"P": round(p, 3), "R": round(r, 3), "F1": round(f1, 3)}
        macro += f1
    out["macro_F1"] = round(macro / 3, 3)
    return out


def main():
    print(f"Loading KLUE-NER dev × {MAX_SAMPLES} and {CKPT}...")
    ds = load_dataset("klue", "ner", split="validation")
    label_names = ds.features["ner_tags"].feature.names
    samples = list(ds)[:MAX_SAMPLES]

    device = 0 if torch.cuda.is_available() else -1
    nlp = pipeline("ner", model=CKPT, tokenizer=CKPT,
                   device=device, aggregation_strategy="simple")

    modes = {
        "v1 baseline": [],
        "v2 + addr_merge_v1": [],
        "v3a + addr_merge_v2": [],
        "v3b + addr_merge_v2 + org_dict": [],
    }
    gold_list = []

    print("\nProcessing 200 samples...")
    for i, sample in enumerate(samples):
        sentence = "".join(sample["tokens"])
        gold = build_gold_spans(sample, label_names)
        gold_list.append(gold)

        # baseline
        baseline = predict_spans(nlp, sentence)
        modes["v1 baseline"].append(baseline)

        # v2: simple addr_merge (이전 스크립트 로직)
        addr = sorted([s for s in baseline if s[2] == "ADDRESS"])
        other = [s for s in baseline if s[2] != "ADDRESS"]
        merged_v1 = []
        if addr:
            cs, ce, ct = addr[0]
            for s, e, t in addr[1:]:
                gap = sentence[ce:s]
                if len(gap.strip()) <= 5 and not any(c in gap for c in ".!?\n"):
                    ce = e
                else:
                    merged_v1.append((cs, ce, ct))
                    cs, ce, ct = s, e, t
            merged_v1.append((cs, ce, ct))
        modes["v2 + addr_merge_v1"].append(other + merged_v1)

        # v3a: addr_merge_v2 (행정구역 hierarchy + 도로명·번지·동호수)
        v3a = merge_address_spans_v2(baseline, sentence)
        modes["v3a + addr_merge_v2"].append(v3a)

        # v3b: + ORG 사전 보강
        org_dict_spans = find_org_dict_spans(sentence)
        v3b = merge_with_dict(v3a, org_dict_spans, sentence)
        modes["v3b + addr_merge_v2 + org_dict"].append(v3b)

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{MAX_SAMPLES}")

    # 메트릭 계산 + 출력
    print(f"\n\n{'='*82}")
    print(f"  Leo97 + 후처리 v3 결과 (KLUE-NER dev × {MAX_SAMPLES})")
    print(f"{'='*82}")
    print(f"  {'Mode':<38} {'NAME':<8} {'ADDR':<8} {'ORG':<8} {'macro':<8}")
    print(f"  {'-'*38} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    results = {}
    for mode, pred_list in modes.items():
        m = compute_metrics(pred_list, gold_list)
        results[mode] = m
        print(f"  {mode:<38} "
              f"{m['NAME']['F1']:<8.3f} "
              f"{m['ADDRESS']['F1']:<8.3f} "
              f"{m['ORG']['F1']:<8.3f} "
              f"{m['macro_F1']:<8.3f}")

    final = results["v3b + addr_merge_v2 + org_dict"]["macro_F1"]
    print(f"\n{'='*82}")
    if final >= 0.75:
        print(f"  ✅ A-primary 확정 — Leo97 + v3 후처리, macro-F1 = {final}")
        print(f"     C-fallback 발동 X. NER 학습 안 해도 됨.")
    elif final >= 0.65:
        print(f"  ⚠ macro-F1 = {final} — 0.75 미달. 추가 옵션:")
        print(f"     1. ADDRESS-only mini fine-tune (1~2일)")
        print(f"     2. C-fallback 풀학습 (2~3일, GPU 필요)")
        print(f"     3. 외부 평가셋(KoJailFuzz) 측정 후 판단")
    else:
        print(f"  ❌ C-fallback 권고 (macro-F1 = {final})")

    out_path = Path(__file__).parent / "../reports/eval_v3.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"\n📁 Saved: {out_path.resolve()}")


if __name__ == "__main__":
    main()
