"""
Phase 3 — A.2 Layer 0 Ablation Study

Decompose Layer 0 into:
  - Mode N (Normalizer only): 13-stage Korean text normalization, no keyword/regex detection
  - Mode D (Detector only):   42 regex patterns + 22 keyword dictionaries on raw text
  - Mode F (Full = current):  Normalize → then Detect on normalized text

Uses existing eval_10k data's per-case mutated text. For each config
(A Baseline, +Norm, +Dict, +Full=C), compute TRUE detection by combining
Layer 0's simulated action with the stored L1~L3 results.
"""
import json
import sys
import re
from collections import defaultdict

sys.path.insert(0, "c:/My-AI-Security-Project/PII/layer_0")
sys.stdout.reconfigure(encoding="utf-8")

from korean_normalizer import KoreanNormalizer
from korean_pii_detector import KoreanPIIDetector

normalizer = KoreanNormalizer()
detector = KoreanPIIDetector()

BASELINE_FILE = "eval_10k_l1l3.json"  # has L1~L3 results per case
BASE3 = {"Presidio PII", "Bedrock Guardrail", "Lakera"}


def is_pii_in_text(pii, text):
    if not pii or not text: return False
    if pii in text: return True
    pd = re.sub(r"\D", "", pii); td = re.sub(r"\D", "", text)
    return len(pd) >= 6 and pd in td


def neutralized_via_layer(lr, mutated, pii):
    if lr.get("error") or lr.get("action") == "ERROR":
        return False
    out = lr.get("output", "")
    if out == "[BLOCKED]": return True
    if not out or out == mutated: return False
    return not is_pii_in_text(pii, out)


def simulate_l0_modes(mutated, pii, threshold=1):
    """Return per-mode 'did Layer 0 neutralize'? (BLOCK or effectively mask)."""
    normalized = normalizer.normalize(mutated)

    # Mode N: normalization only → output = normalized, no BLOCK
    mode_n_neutralized = (normalized != mutated) and not is_pii_in_text(pii, normalized)

    # Mode D: detector only on raw mutated text
    findings_raw = detector.detect(mutated)
    mode_d_neutralized = len(findings_raw) >= threshold

    # Mode F: normalize then detect on normalized
    findings_norm = detector.detect(normalized)
    mode_f_blocked = len(findings_norm) >= threshold
    mode_f_neutralized = mode_f_blocked or ((normalized != mutated) and not is_pii_in_text(pii, normalized))

    return {
        "N": mode_n_neutralized,
        "D": mode_d_neutralized,
        "F": mode_f_neutralized,
    }


def main():
    cases = json.load(open(BASELINE_FILE, "r", encoding="utf-8"))["results"]
    print(f"Loaded {len(cases)} cases from {BASELINE_FILE}")

    # Per-slice stats
    slices = {
        "overall": lambda c: True,
        "EN": lambda c: c.get("lang") == "EN",
        "KR": lambda c: c.get("lang") == "KR",
        "KR_checksum": lambda c: c.get("lang") == "KR" and c.get("validity_group") == "checksum",
        "KR_format":   lambda c: c.get("lang") == "KR" and c.get("validity_group") == "format",
        "KR_semantic": lambda c: c.get("lang") == "KR" and c.get("validity_group") == "semantic",
    }

    counts = defaultdict(lambda: {
        "n": 0, "A": 0, "A+N": 0, "A+D": 0, "A+F": 0,
    })

    for case in cases:
        pii = case.get("pii_value", "") or case.get("original", "") or ""
        mutated = case.get("mutated", "")

        # Baseline (L1~L3) neutralized?
        baseline_true = False
        for lr in case.get("layer_results", []):
            if lr["layer"] in BASE3 and neutralized_via_layer(lr, mutated, pii):
                baseline_true = True
                break

        # L0 simulation
        l0 = simulate_l0_modes(mutated, pii)

        for name, pred in slices.items():
            if not pred(case): continue
            s = counts[name]
            s["n"] += 1
            if baseline_true: s["A"] += 1
            if baseline_true or l0["N"]: s["A+N"] += 1
            if baseline_true or l0["D"]: s["A+D"] += 1
            if baseline_true or l0["F"]: s["A+F"] += 1

    print("\n" + "=" * 90)
    print("  Phase 3 — A.2 Layer 0 Ablation Study (TRUE detection, 10k)")
    print("=" * 90)
    print(f"\n  Mode N = Normalizer only (13-stage Korean normalization)")
    print(f"  Mode D = Detector only (42 regex + 22 keyword dicts on raw text)")
    print(f"  Mode F = Full (Normalize → then Detect) — current production")

    print(f"\n  {'Slice':14s} {'n':>6s} {'A (base)':>10s} {'A+N':>10s} {'A+D':>10s} {'A+F':>10s}  {'N only':>8s} {'D only':>8s} {'F only':>8s}")
    print("-" * 110)
    result = {}
    for name, s in counts.items():
        n = s["n"]
        a = 100 * s["A"] / n
        an = 100 * s["A+N"] / n
        ad = 100 * s["A+D"] / n
        af = 100 * s["A+F"] / n
        n_gain = an - a
        d_gain = ad - a
        f_gain = af - a
        print(f"  {name:14s} {n:>6d} {a:>9.2f}% {an:>9.2f}% {ad:>9.2f}% {af:>9.2f}%  {n_gain:>+6.2f}%p {d_gain:>+6.2f}%p {f_gain:>+6.2f}%p")
        result[name] = {
            "n": n,
            "A_baseline": round(a, 2),
            "A_plus_N": round(an, 2),  "N_gain": round(n_gain, 2),
            "A_plus_D": round(ad, 2),  "D_gain": round(d_gain, 2),
            "A_plus_F": round(af, 2),  "F_gain": round(f_gain, 2),
        }

    print(f"\nInterpretation (KR_semantic — core narrative slice):")
    ks = result.get("KR_semantic", {})
    if ks:
        print(f"  Baseline:    {ks['A_baseline']}%")
        print(f"  + Norm only: {ks['A_plus_N']}%  (gain {ks['N_gain']:+.2f}%p — L1~L3가 정규화된 텍스트를 더 잘 잡는 효과)")
        print(f"  + Dict only: {ks['A_plus_D']}%  (gain {ks['D_gain']:+.2f}%p — 키워드 사전이 직접 잡는 효과)")
        print(f"  + Full:      {ks['A_plus_F']}%  (gain {ks['F_gain']:+.2f}%p — 둘 다 합친 현재 동작)")
        print(f"\n  → Norm 단독 기여: {ks['N_gain']:+.2f}%p")
        print(f"  → Dict 단독 기여: {ks['D_gain']:+.2f}%p")
        print(f"  → 시너지 (F - N - D): {ks['F_gain'] - ks['N_gain'] - ks['D_gain']:+.2f}%p")

    json.dump(result, open("phase3_ablation.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nSaved: phase3_ablation.json")


if __name__ == "__main__":
    main()
