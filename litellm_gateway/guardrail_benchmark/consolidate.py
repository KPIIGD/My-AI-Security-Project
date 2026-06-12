"""모든 result_*.json → 6개 시스템 × 3 split 종합표 (엑셀 + 콘솔).

출력: benchmark_summary.xlsx (split별 시트 + 종합 시트), 콘솔 표.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SPLITS = ("test", "klue_test", "val")
ORDER = ["our_ner", "naver_ner", "modu_ner", "bedrock", "ai4privacy", "presidio"]
LABEL = {"our_ner": "our_ner (우리 v3)", "naver_ner": "naver_ner (로컬)",
         "modu_ner": "modu_ner (로컬)", "bedrock": "bedrock (AWS)",
         "ai4privacy": "ai4privacy (영어PII)", "presidio": "presidio (영어)"}


def load(fname: str) -> dict:
    p = HERE / fname
    return json.loads(p.read_text(encoding="utf-8"))["systems"] if p.exists() else {}


def pct(cell) -> str:
    c, t = cell
    return f"{100*c/t:.1f}%" if t else "-"


def collect_split(split: str) -> dict:
    sysd = {}
    sysd.update(load(f"result_ourpres_{split}.json"))   # our_ner, presidio
    sysd.update(load(f"result_bedrock_{split}.json"))    # bedrock
    sysd.update(load(f"result_local_{split}.json"))      # modu/naver/ai4privacy
    return sysd


def main() -> None:
    sheets = {}
    print("\n" + "=" * 70)
    for split in SPLITS:
        sysd = collect_split(split)
        rows = []
        for s in ORDER:
            if s not in sysd:
                continue
            m = sysd[s]
            rows.append({"시스템": LABEL[s], "NAME": pct(m["NAME"]), "ADDRESS": pct(m["ADDRESS"]),
                         "ORG": pct(m["ORG"]), "전체 recall": f"{100*m['overall_recall']:.1f}%",
                         "_sort": m["overall_recall"]})
        rows.sort(key=lambda r: -r["_sort"])
        df = pd.DataFrame([{k: v for k, v in r.items() if k != "_sort"} for r in rows])
        sheets[split] = df
        print(f"\n### {split}  (PII 문장 1,000건)")
        print(df.to_string(index=False))

    # FULL our_ner/presidio (12,841)
    mx = load("result_max.json")
    if mx:
        print("\n### ALL (전체 12,841건) — our_ner / presidio")
        for s in ("our_ner", "presidio"):
            m = mx[s]
            print(f"  {LABEL[s]:24} NAME {pct(m['NAME'])}  ADDRESS {pct(m['ADDRESS'])}  "
                  f"ORG {pct(m['ORG'])}  전체 {100*m['overall_recall']:.1f}%")

    # 엑셀
    with pd.ExcelWriter(HERE / "benchmark_summary.xlsx", engine="openpyxl") as w:
        for split, df in sheets.items():
            df.to_excel(w, sheet_name=split, index=False)
        if mx:
            mrows = [{"시스템": LABEL[s], "NAME": pct(mx[s]["NAME"]), "ADDRESS": pct(mx[s]["ADDRESS"]),
                      "ORG": pct(mx[s]["ORG"]), "전체 recall": f"{100*mx[s]['overall_recall']:.1f}%",
                      "표본": "12,841(전체)"} for s in ("our_ner", "presidio")]
            pd.DataFrame(mrows).to_excel(w, sheet_name="ALL_full", index=False)
    print(f"\n→ {HERE / 'benchmark_summary.xlsx'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
