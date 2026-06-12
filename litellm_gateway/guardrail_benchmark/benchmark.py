"""한국어 PII 가드레일 recall 벤치마크 (이식 가능·독립).

우리 gold(NAME/ADDRESS/ORG) 평가셋을 여러 가드레일에 통과시켜 **타입별 recall** 비교.
recall = 우리가 라벨한 PII 중 그 시스템이 잡은 비율 (높을수록 PII 탐지력 ↑).
매칭 = gold span 과 같은 타입 span 이 overlap 하면 catch(관대).

이 폴더(eval_gold.jsonl + benchmark.py)만 있으면 다른 세션/PC 에서도 돈다.

═══════════════════════════════════════════════════════════════════
🔌 새 가드레일 추가하는 법 (3단계):
  1. 아래 ADAPTERS 에 함수 추가: text → [(start, end, "NAME"/"ADDRESS"/"ORG"), ...]
     - 그 시스템의 entity_type 을 우리 3타입으로 매핑 (없는 타입은 버림)
  2. 시스템 엔드포인트/키는 함수 안에서 env 나 상수로 읽기
  3. 실행: python benchmark.py --systems our_ner,presidio,<새이름>
═══════════════════════════════════════════════════════════════════

사용:
  python benchmark.py --self-test                       # 오프라인 로직 검증
  python benchmark.py --systems our_ner,presidio --split test --n 500
  python benchmark.py --systems our_ner --split klue_test --save results.json
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path

GOLD = Path(__file__).resolve().parent / "eval_gold.jsonl"
CANON = ("NAME", "ADDRESS", "ORG")


def _post(url: str, payload: dict, timeout: int = 20):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


# ═══════════════ 가드레일 어댑터 (여기에 추가) ═══════════════

# (1) 우리 NER 사이드카 — localhost:8080/v1/pii/apply
_OUR_URL = os.environ.get("OUR_NER_URL", "http://localhost:8080")
_OUR_MAP = {"PERSON_NAME": "NAME", "ADDRESS_FULL": "ADDRESS", "ADDRESS_UNIT": "ADDRESS",
            "ORGANIZATION": "ORG", "SCHOOL": "ORG", "HOSPITAL": "ORG"}


def adapter_our_ner(text: str) -> list[tuple[int, int, str]]:
    d = _post(f"{_OUR_URL}/v1/pii/apply", {"text": text, "scan_stage": "input"})
    out = []
    for s in d.get("spans") or d.get("pii_spans") or []:
        ct = _OUR_MAP.get(s.get("entity_type") or s.get("type") or "")
        if ct and "start" in s and "end" in s:
            out.append((s["start"], s["end"], ct))
    return out


# (2) Microsoft Presidio — localhost:5001/analyze. ko recognizer 없어 en 호출.
_PRESIDIO_URL = os.environ.get("PRESIDIO_URL", "http://localhost:5001")
_PRESIDIO_LANG = os.environ.get("PRESIDIO_LANG", "en")
_PRESIDIO_MAP = {"PERSON": "NAME", "NRP": "NAME", "LOCATION": "ADDRESS", "GPE": "ADDRESS",
                 "ADDRESS": "ADDRESS", "ORGANIZATION": "ORG", "ORG": "ORG"}


def adapter_presidio(text: str) -> list[tuple[int, int, str]]:
    arr = _post(f"{_PRESIDIO_URL}/analyze", {"text": text, "language": _PRESIDIO_LANG})
    out = []
    for e in arr or []:
        ct = _PRESIDIO_MAP.get(e.get("entity_type", ""))
        if ct:
            out.append((e["start"], e["end"], ct))
    return out


# (3) 템플릿 — 새 가드레일 추가 예시 (AWS Comprehend / Bedrock / Azure 등)
# def adapter_comprehend(text: str) -> list[tuple[int, int, str]]:
#     import boto3
#     r = boto3.client("comprehend").detect_pii_entities(Text=text, LanguageCode="ko")
#     MAP = {"NAME": "NAME", "ADDRESS": "ADDRESS"}  # Comprehend 타입 → 우리 3타입
#     return [(e["BeginOffset"], e["EndOffset"], MAP[e["Type"]])
#             for e in r["Entities"] if e["Type"] in MAP]

# (3) AWS Bedrock Guardrail — ApplyGuardrail. offset 미제공 → match 문자열을 문장에서 검색.
#   Bedrock PII 타입엔 ORGANIZATION 없음 → ORG 는 구조적으로 0 (논문 포인트).
#   AWS 키는 C:\tmp\bedrock.env (컨테이너 env 추출) 또는 os.environ 에서.
_BEDROCK_ENV = os.environ.get("BEDROCK_ENV_FILE", r"C:\tmp\bedrock.env")
_BEDROCK_MAP = {"NAME": "NAME", "ADDRESS": "ADDRESS"}  # ORG 타입 없음
_bedrock_client = None
_bedrock_gid = None


def _bedrock_init():
    global _bedrock_client, _bedrock_gid
    if _bedrock_client is not None:
        return
    if os.path.exists(_BEDROCK_ENV):
        for line in open(_BEDROCK_ENV, encoding="utf-8"):
            if "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)
    import boto3
    _bedrock_gid = os.environ["BEDROCK_GUARDRAIL_ID"]
    _bedrock_client = boto3.client("bedrock-runtime",
                                   region_name=os.environ.get("AWS_REGION", "us-east-1"))


def _find_spans(text: str, match: str, ctype: str) -> list[tuple[int, int, str]]:
    """match 문자열의 모든 비중복 출현 위치 → span. (Bedrock 은 offset 미제공)"""
    out, i = [], 0
    if not match:
        return out
    while True:
        j = text.find(match, i)
        if j < 0:
            break
        out.append((j, j + len(match), ctype)); i = j + len(match)
    return out


def adapter_bedrock(text: str) -> list[tuple[int, int, str]]:
    _bedrock_init()
    r = _bedrock_client.apply_guardrail(
        guardrailIdentifier=_bedrock_gid, guardrailVersion="DRAFT",
        source="INPUT", content=[{"text": {"text": text}}])
    out = []
    for a in r.get("assessments", []):
        for e in a.get("sensitiveInformationPolicy", {}).get("piiEntities", []):
            ct = _BEDROCK_MAP.get(e.get("type", ""))
            if ct:
                out += _find_spans(text, e.get("match", ""), ct)
    return out


# (4) 로컬 HF NER 모델 (transformers, 무료·오프라인) — 한국어 NER 비교 baseline.
#   로컬 HF 캐시에 이미 받아둔 모델 사용. 모델별 라벨 → 우리 3타입 매핑.
_HF_PIPES = {}


def _hf_pipe(model_id, agg):
    key = (model_id, agg)
    if key not in _HF_PIPES:
        from transformers import pipeline
        import torch
        _HF_PIPES[key] = pipeline("token-classification", model=model_id,
                                  aggregation_strategy=agg,
                                  device=0 if torch.cuda.is_available() else -1)
    return _HF_PIPES[key]


def _hf_simple_adapter(model_id, mapping):
    """aggregation=simple 으로 충분한 표준 BIO(B-PER) 모델용."""
    def adapter(text):
        out = []
        for e in _hf_pipe(model_id, "simple")(text):
            ct = mapping.get(e["entity_group"])
            if ct:
                out.append((e["start"], e["end"], ct))
        return out
    return adapter


def _hf_suffix_bio_adapter(model_id, mapping):
    """라벨이 'PER-B'/'PER-I' 접미 BIO → 직접 병합 (HF 기본 병합이 못 함)."""
    def adapter(text):
        spans, cur = [], None
        for t in _hf_pipe(model_id, "none")(text):
            lab = t.get("entity") or "O"
            ent, bi = (lab.rsplit("-", 1) + ["B"])[:2] if "-" in lab else (lab, "B")
            ct = mapping.get(ent)
            if ct and bi == "B":
                if cur:
                    spans.append(tuple(cur))
                cur = [t["start"], t["end"], ct]
            elif ct and bi == "I" and cur and cur[2] == ct:
                cur[1] = t["end"]
            else:
                if cur:
                    spans.append(tuple(cur)); cur = None
        if cur:
            spans.append(tuple(cur))
        return spans
    return adapter


_MODU_MAP = {"PS": "NAME", "LC": "ADDRESS", "OG": "ORG"}
_NAVER_MAP = {"PER": "NAME", "LOC": "ADDRESS", "ORG": "ORG"}
_AI4P_MAP = {"FIRSTNAME": "NAME", "LASTNAME": "NAME", "MIDDLENAME": "NAME", "PREFIX": "NAME",
             "STREET": "ADDRESS", "CITY": "ADDRESS", "STATE": "ADDRESS", "COUNTY": "ADDRESS",
             "BUILDINGNUMBER": "ADDRESS", "ZIPCODE": "ADDRESS", "SECONDARYADDRESS": "ADDRESS",
             "COMPANYNAME": "ORG"}

ADAPTERS = {
    "our_ner": adapter_our_ner,
    "presidio": adapter_presidio,
    "bedrock": adapter_bedrock,
    "modu_ner": _hf_simple_adapter("Leo97/KoELECTRA-small-v3-modu-ner", _MODU_MAP),
    "naver_ner": _hf_suffix_bio_adapter("monologg/koelectra-base-v3-naver-ner", _NAVER_MAP),
    "ai4privacy": _hf_simple_adapter("Isotonic/deberta-v3-base_finetuned_ai4privacy_v2", _AI4P_MAP),
    # "comprehend": adapter_comprehend,   # 위 템플릿 풀어서 등록
}

# ═══════════════════════════════════════════════════════════════


def _overlap(a, b) -> bool:
    return a[2] == b[2] and a[0] < b[1] and b[0] < a[1]


def _score(gold, pred) -> dict:
    res = {t: [0, 0] for t in CANON}
    for g in gold:
        res[g[2]][1] += 1
        if any(_overlap(g, p) for p in pred):
            res[g[2]][0] += 1
    return res


def run(systems: list[str], split: str | None, n: int, save: str | None) -> None:
    rows = [json.loads(l) for l in GOLD.read_text(encoding="utf-8").splitlines() if l.strip()]
    if split:
        rows = [r for r in rows if r["split"] == split]
    rows = [r for r in rows if r["spans"]][:n]   # PII 있는 문장만 (recall 대상)
    print(f"평가셋: {split or 'all'} 중 PII 있는 문장 {len(rows):,}건\n")

    agg = {s: {**{t: [0, 0] for t in CANON}, "err": 0} for s in systems}
    for r in rows:
        gold = [(s["start"], s["end"], s["type"]) for s in r["spans"]]
        for sys_name in systems:
            try:
                pred = ADAPTERS[sys_name](r["sentence"])
            except Exception:
                agg[sys_name]["err"] += 1
                continue
            sc = _score(gold, pred)
            for t in CANON:
                agg[sys_name][t][0] += sc[t][0]; agg[sys_name][t][1] += sc[t][1]

    print(f"{'시스템':14} {'NAME':>14} {'ADDRESS':>14} {'ORG':>14} {'전체':>16}  err")
    print("-" * 82)
    out = {}
    for s in systems:
        a = agg[s]; tc = tt = 0; cells = []
        for t in CANON:
            c, tot = a[t]; tc += c; tt += tot
            cells.append(f"{(100*c/tot if tot else 0):5.1f}% ({c}/{tot})")
        overall = f"{(100*tc/tt if tt else 0):5.1f}% ({tc}/{tt})"
        print(f"{s:14} {cells[0]:>14} {cells[1]:>14} {cells[2]:>14} {overall:>16}  {a['err']}")
        out[s] = {"NAME": a["NAME"], "ADDRESS": a["ADDRESS"], "ORG": a["ORG"],
                  "overall_recall": (tc / tt if tt else 0), "errors": a["err"]}
    print("\n(recall = 우리가 라벨한 PII 중 그 시스템이 잡은 비율)")
    if save:
        Path(save).write_text(json.dumps({"split": split, "n": len(rows), "systems": out},
                                         ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"→ 저장: {save}")


def self_test() -> None:
    gold = [(0, 3, "NAME"), (5, 9, "ORG")]
    assert _score(gold, [(0, 3, "NAME")]) == {"NAME": [1, 1], "ADDRESS": [0, 0], "ORG": [0, 1]}
    print("✅ self-test 통과 (recall 채점 로직 정상)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", default="our_ner,presidio")
    ap.add_argument("--split", default="test", help="val/test/klue_test (생략=전체)")
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--save", default=None, help="결과 JSON 저장 경로")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test(); return
    if not GOLD.exists():
        raise SystemExit(f"gold 없음: {GOLD} — 먼저 'python export_eval_gold.py' 실행")
    systems = [s.strip() for s in args.systems.split(",") if s.strip() in ADAPTERS]
    run(systems, args.split if args.split != "all" else None, args.n, args.save)


if __name__ == "__main__":
    main()
