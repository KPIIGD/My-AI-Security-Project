"""우리 PII 라벨 데이터 → 다른 가드레일 recall 벤치마크.

사용자 트랙2: "우리 학습데이터를 다른 가드레일에 넣고 얼마나 PII 잡는지 테스트".
우리 gold(NAME/ADDRESS/ORG span)를 정답으로 삼아, 각 시스템에 문장을 통과시켜
**같은 PII를 잡았는지(recall)** 를 타입별로 측정한다.

비교 시스템 (어댑터):
  - our_ner  : 우리 NER 사이드카 (localhost:8080/v1/pii/apply)
  - presidio : Microsoft Presidio analyzer (localhost:5001/analyze, language=ko)
  - (확장) bedrock/comprehend 등은 어댑터만 추가하면 됨.

평가 = recall 중심(우리가 라벨한 PII를 잡았나). precision 은 우리 gold 가 3타입뿐이라
       불공정(상대는 phone/email 도 잡음) → recall 로 "PII 탐지력" 비교.
매칭 = gold span 과 같은 canon 타입 span 이 **overlap** 하면 catch(관대한 recall).

⚠️ Docker(presidio/사이드카) 가 떠 있어야 실제 실행. 코드 검증은 --self-test(네트워크 0).

사용 (PowerShell, C:/litellm):
  python guardrail_recall_benchmark.py --self-test            # 로직 검증(오프라인)
  python guardrail_recall_benchmark.py --n 500 --systems our_ner,presidio
  python guardrail_recall_benchmark.py --n 500 --split klue_test --presidio-url http://localhost:5002
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

GOLD_FILE = Path(r"C:\My-AI-Security-Project\PII\ner\data\pii_ner_v4_full.json")

# 각 시스템 entity_type → canon(NAME/ADDRESS/ORG)
OUR_MAP = {"PERSON_NAME": "NAME", "ADDRESS_FULL": "ADDRESS", "ADDRESS_UNIT": "ADDRESS",
           "ORGANIZATION": "ORG", "SCHOOL": "ORG", "HOSPITAL": "ORG"}
PRESIDIO_MAP = {"PERSON": "NAME", "NRP": "NAME", "LOCATION": "ADDRESS", "GPE": "ADDRESS",
                "ADDRESS": "ADDRESS", "ORGANIZATION": "ORG", "ORG": "ORG"}


def _post(url: str, payload: dict, timeout: int = 20):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def adapter_our_ner(text: str, base: str) -> list[tuple[int, int, str]]:
    d = _post(f"{base}/v1/pii/apply", {"text": text, "scan_stage": "input"})
    spans = d.get("spans") or d.get("pii_spans") or []
    out = []
    for s in spans:
        ct = OUR_MAP.get(s.get("entity_type") or s.get("type") or "")
        if ct and "start" in s and "end" in s:
            out.append((s["start"], s["end"], ct))
    return out


# Presidio 는 ko recognizer 가 없어 'ko'는 500. 'en'으로 호출(언어무관 패턴만 잡힘
# → 한국어 NAME/ADDRESS/ORG 는 거의 0 = 영어중심 가드레일 한계 입증).
PRESIDIO_LANG = "en"


def adapter_presidio(text: str, base: str) -> list[tuple[int, int, str]]:
    arr = _post(f"{base}/analyze", {"text": text, "language": PRESIDIO_LANG})
    out = []
    for e in arr or []:
        ct = PRESIDIO_MAP.get(e.get("entity_type", ""))
        if ct:
            out.append((e["start"], e["end"], ct))
    return out


ADAPTERS = {"our_ner": adapter_our_ner, "presidio": adapter_presidio}


def gold_spans(ex: dict) -> list[tuple[int, int, str]]:
    """label_names(char-level) → [(start,end,type)]. 토큰=list(sentence)라 idx=char offset."""
    labs = ex["label_names"]
    out = []
    s = t = None
    for i, l in enumerate(labs):
        if l.startswith("B-"):
            if s is not None:
                out.append((s, i, t))
            s, t = i, l[2:]
        elif l.startswith("I-") and s is not None and l[2:] == t:
            continue
        else:
            if s is not None:
                out.append((s, i, t)); s = t = None
    if s is not None:
        out.append((s, len(labs), t))
    return out


def _overlap(a: tuple[int, int, str], b: tuple[int, int, str]) -> bool:
    return a[2] == b[2] and a[0] < b[1] and b[0] < a[1]


def score(gold: list, pred: list) -> dict[str, list[int]]:
    """타입별 [caught, total]."""
    res = {"NAME": [0, 0], "ADDRESS": [0, 0], "ORG": [0, 0]}
    for g in gold:
        res[g[2]][1] += 1
        if any(_overlap(g, p) for p in pred):
            res[g[2]][0] += 1
    return res


def run(systems: list[str], split: str, n: int, *, our_url: str, presidio_url: str) -> None:
    data = json.loads(GOLD_FILE.read_text(encoding="utf-8"))
    rows = [ex for ex in data.get(split, []) if gold_spans(ex)][:n]  # PII 있는 문장만
    print(f"평가셋: {split} 중 PII 있는 문장 {len(rows):,}건\n")

    url = {"our_ner": our_url, "presidio": presidio_url}
    agg = {s: {"NAME": [0, 0], "ADDRESS": [0, 0], "ORG": [0, 0], "err": 0} for s in systems}
    for ex in rows:
        gold = gold_spans(ex)
        for s in systems:
            try:
                pred = ADAPTERS[s](ex["sentence"], url[s])
            except Exception:
                agg[s]["err"] += 1
                continue
            sc = score(gold, pred)
            for t in ("NAME", "ADDRESS", "ORG"):
                agg[s][t][0] += sc[t][0]; agg[s][t][1] += sc[t][1]

    print(f"{'시스템':12} {'NAME':>14} {'ADDRESS':>14} {'ORG':>14} {'전체':>14}  err")
    print("-" * 78)
    for s in systems:
        a = agg[s]
        cells = []
        tc = tt = 0
        for t in ("NAME", "ADDRESS", "ORG"):
            c, tot = a[t]; tc += c; tt += tot
            cells.append(f"{(100*c/tot if tot else 0):5.1f}% ({c}/{tot})")
        overall = f"{(100*tc/tt if tt else 0):5.1f}% ({tc}/{tt})"
        print(f"{s:12} {cells[0]:>14} {cells[1]:>14} {cells[2]:>14} {overall:>14}  {a['err']}")
    print("\n(recall = 우리가 라벨한 PII 중 그 시스템이 잡은 비율. 높을수록 PII 탐지력 ↑)")


def self_test() -> None:
    """오프라인 로직 검증 — 가짜 시스템으로 gold추출+scoring 확인."""
    ex = {"sentence": "홍길동은 삼성전자 다녀요",
          "label_names": list("B-NAME I-NAME I-NAME O O B-ORG I-ORG I-ORG I-ORG O O O O".split())}
    # 위 label_names 는 char 수와 안 맞으니 직접 구성
    sent = "홍길동은 삼성전자 다녀요"
    labs = ["O"] * len(sent)
    labs[0] = "B-NAME"; labs[1] = "I-NAME"; labs[2] = "I-NAME"   # 홍길동
    labs[5] = "B-ORG"; labs[6] = "I-ORG"; labs[7] = "I-ORG"; labs[8] = "I-ORG"  # 삼성전자
    ex = {"sentence": sent, "label_names": labs}
    g = gold_spans(ex)
    assert (0, 3, "NAME") in g and (5, 9, "ORG") in g, g
    # 시스템이 NAME만 잡았다고 가정
    pred = [(0, 3, "NAME")]
    sc = score(g, pred)
    assert sc["NAME"] == [1, 1] and sc["ORG"] == [0, 1], sc
    print("✅ self-test 통과: gold추출", g, "| NAME만 잡은 시스템 recall:",
          f"NAME {sc['NAME']}, ORG {sc['ORG']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", default="our_ner,presidio")
    ap.add_argument("--split", default="test", help="gold split (test/klue_test/val)")
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--our-url", default="http://localhost:8080")
    ap.add_argument("--presidio-url", default="http://localhost:5001")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test(); return
    systems = [s.strip() for s in args.systems.split(",") if s.strip() in ADAPTERS]
    run(systems, args.split, args.n, our_url=args.our_url, presidio_url=args.presidio_url)


if __name__ == "__main__":
    main()
