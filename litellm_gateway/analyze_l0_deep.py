"""
Deep dive into Layer 0 effect:
1. L0 solo catches breakdown (which PII types did L0 single-handedly save?)
2. Remaining 627 real_bypasses with L0 (where does L0 still fail?)
3. Potential L0 false positives (L0 acted on English-only PII)
4. L0 contribution per mutation level
"""
import json
import sys
import re
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding="utf-8")

L0_NAME = "korean-layer0"
BASE3 = {"Presidio PII", "Bedrock Guardrail", "Lakera"}


def is_pii_in_text(pii_value, text):
    if not pii_value or not text:
        return False
    if pii_value in text:
        return True
    pii_digits = re.sub(r"\D", "", pii_value)
    text_digits = re.sub(r"\D", "", text)
    if len(pii_digits) >= 6 and pii_digits in text_digits:
        return True
    fullwidth_map = {chr(0xFF10 + i): str(i) for i in range(10)}
    text_norm = "".join(fullwidth_map.get(c, c) for c in text)
    if pii_value in text_norm:
        return True
    text_digits_norm = re.sub(r"\D", "", text_norm)
    if len(pii_digits) >= 6 and pii_digits in text_digits_norm:
        return True
    return False


def neutralized(lr, mutated, pii):
    if lr.get("error") or lr.get("action") == "ERROR":
        return False
    output = lr.get("output", "")
    if output == "[BLOCKED]":
        return True
    if not output or output == mutated:
        return False
    return not is_pii_in_text(pii, output)


def analyze():
    cases = json.load(open("eval_10k_l0_l1l3.json", "r", encoding="utf-8"))["results"]

    # Bucket cases
    l0_solo = []  # L0 caught, others didn't
    l0_with_others = []  # L0 caught + at least one other
    others_only = []  # L0 missed, but others caught
    all_missed = []  # everyone missed
    l0_false_positive_candidates = []  # L0 acted on EN-only case

    l0_solo_by_pii = Counter()
    l0_solo_by_validity = Counter()
    l0_solo_by_mutation = Counter()
    remaining_bypass_by_pii = Counter()
    remaining_bypass_by_validity = Counter()
    remaining_bypass_by_mutation = Counter()
    en_l0_actions = []

    for c in cases:
        pii = c.get("pii_value", "") or c.get("original", "") or ""
        mutated = c.get("mutated", "")
        lang = c.get("lang")

        l0_caught = False
        others_caught = False
        l0_action = None
        for lr in c.get("layer_results", []):
            if lr["layer"] == L0_NAME:
                l0_action = lr.get("action")
                if neutralized(lr, mutated, pii):
                    l0_caught = True
            elif lr["layer"] in BASE3:
                if neutralized(lr, mutated, pii):
                    others_caught = True

        if l0_caught and not others_caught:
            l0_solo.append(c)
            l0_solo_by_pii[c.get("pii_type")] += 1
            l0_solo_by_validity[c.get("validity_group")] += 1
            l0_solo_by_mutation[c.get("mutation_level")] += 1
        elif l0_caught and others_caught:
            l0_with_others.append(c)
        elif not l0_caught and others_caught:
            others_only.append(c)
        else:
            all_missed.append(c)
            remaining_bypass_by_pii[c.get("pii_type")] += 1
            remaining_bypass_by_validity[c.get("validity_group")] += 1
            remaining_bypass_by_mutation[c.get("mutation_level")] += 1

        # L0 acted on EN — potential false positive (L0 is Korean-only by design)
        if lang == "EN" and l0_action in ("BLOCK", "MASK"):
            en_l0_actions.append({
                "id": c.get("id"),
                "pii_type": c.get("pii_type"),
                "mutation": c.get("mutation_name"),
                "mutated": mutated[:120],
                "l0_action": l0_action,
            })

    print("=" * 78)
    print("  Deep-Dive Analysis — Layer 0 effect on 10k")
    print("=" * 78)

    n = len(cases)
    print(f"\nCase outcome breakdown ({n} total):")
    print(f"  L0 solo  (L0 caught, others missed): {len(l0_solo):>5} ({100*len(l0_solo)/n:.2f}%)")
    print(f"  L0 + others (both caught):           {len(l0_with_others):>5} ({100*len(l0_with_others)/n:.2f}%)")
    print(f"  Others only (L0 missed, others ok):  {len(others_only):>5} ({100*len(others_only)/n:.2f}%)")
    print(f"  All missed (real bypass):            {len(all_missed):>5} ({100*len(all_missed)/n:.2f}%)")

    print(f"\n--- L0 SOLO catches by PII type (top 25) ---")
    for t, c in l0_solo_by_pii.most_common(25):
        print(f"  {t:18s} {c}")

    print(f"\n--- L0 SOLO catches by validity_group ---")
    for g, c in sorted(l0_solo_by_validity.items()):
        print(f"  {g:10s} {c}")

    print(f"\n--- L0 SOLO catches by mutation_level ---")
    for lv, c in sorted(l0_solo_by_mutation.items()):
        print(f"  L{lv}  {c}")

    print(f"\n--- Remaining bypasses (everyone missed) by PII type (top 25) ---")
    for t, c in remaining_bypass_by_pii.most_common(25):
        print(f"  {t:18s} {c}")

    print(f"\n--- Remaining bypasses by validity_group ---")
    for g, c in sorted(remaining_bypass_by_validity.items()):
        print(f"  {g:10s} {c}")

    print(f"\n--- Remaining bypasses by mutation_level ---")
    for lv, c in sorted(remaining_bypass_by_mutation.items()):
        print(f"  L{lv}  {c}")

    print(f"\n--- Potential false positives: L0 acted on EN cases ({len(en_l0_actions)} total) ---")
    fp_pii = Counter(x["pii_type"] for x in en_l0_actions)
    fp_mut = Counter(x["mutation"] for x in en_l0_actions)
    print(f"  by pii_type: {dict(fp_pii.most_common(10))}")
    print(f"  by mutation: {dict(fp_mut.most_common(10))}")
    print(f"\n  sample (first 5):")
    for x in en_l0_actions[:5]:
        print(f"    {x['pii_type']:12s} {x['mutation']:14s} {x['l0_action']:5s} : {x['mutated'][:80]!r}")

    # Save
    out = {
        "case_outcomes": {
            "l0_solo": len(l0_solo),
            "l0_with_others": len(l0_with_others),
            "others_only": len(others_only),
            "all_missed": len(all_missed),
        },
        "l0_solo_by_pii": dict(l0_solo_by_pii.most_common()),
        "l0_solo_by_validity": dict(l0_solo_by_validity),
        "l0_solo_by_mutation": dict(l0_solo_by_mutation),
        "remaining_bypass_by_pii": dict(remaining_bypass_by_pii.most_common()),
        "remaining_bypass_by_validity": dict(remaining_bypass_by_validity),
        "remaining_bypass_by_mutation": dict(remaining_bypass_by_mutation),
        "potential_false_positives_count": len(en_l0_actions),
        "fp_by_pii": dict(fp_pii.most_common()),
        "fp_by_mutation": dict(fp_mut.most_common()),
        "fp_samples": en_l0_actions[:30],
    }
    json.dump(out, open("analyze_l0_deep.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nSaved: analyze_l0_deep.json")


if __name__ == "__main__":
    analyze()
