"""
Phase 3 — B.6 L4 Smart Skip Analysis

Question: 만약 L0+L1~L3가 이미 잡은 케이스는 L4를 호출하지 않는다면
         (cascade 최적화), 얼마나 많은 L4 호출을 절감할 수 있는가?
         그리고 detection rate는 얼마나 유지되는가?

D Full (L0~L4) vs SmartCascade (L0+L1~L3 neutralize 안 한 케이스만 L4)
"""
import json
import sys
import re

sys.stdout.reconfigure(encoding="utf-8")

FILE = "eval_10k_l0_l1l4_full.json"
L0 = "korean-layer0"
L4 = "gpt4o-pii-judge"
L1L3 = {"Presidio PII", "Bedrock Guardrail", "Lakera"}
L0L3 = L1L3 | {L0}
ALL5 = L0L3 | {L4}


def is_pii_in_text(pii, text):
    if not pii or not text: return False
    if pii in text: return True
    pd = re.sub(r"\D", "", pii); td = re.sub(r"\D", "", text)
    return len(pd) >= 6 and pd in td


def neutralized(lr, mutated, pii):
    if lr.get("error") or lr.get("action") == "ERROR": return False
    out = lr.get("output", "")
    if out == "[BLOCKED]": return True
    if not out or out == mutated: return False
    return not is_pii_in_text(pii, out)


def true_by_layers(case, layers):
    pii = case.get("pii_value", "") or case.get("original", "") or ""
    mut = case.get("mutated", "")
    for lr in case.get("layer_results", []):
        if lr["layer"] not in layers: continue
        if neutralized(lr, mut, pii): return True
    return False


cases = json.load(open(FILE, "r", encoding="utf-8"))["results"]
print(f"Loaded {len(cases)} cases\n")

# Count: L0+L1~L3 neutralized? L4 contribution?
total = len(cases)
l0l3_true = 0       # L0+L1~L3 가 이미 잡음 → L4 스킵 가능
l4_needed = 0       # L0~L3 놓침 → L4 필요
l4_recovered = 0    # L4가 L0~L3 놓친 케이스를 잡음
l4_missed = 0       # L4도 못 잡음

for c in cases:
    l0l3 = true_by_layers(c, L0L3)
    l4_only = true_by_layers(c, {L4})
    full = true_by_layers(c, ALL5)

    if l0l3:
        l0l3_true += 1
    else:
        l4_needed += 1
        if l4_only:
            l4_recovered += 1
        else:
            l4_missed += 1

# Full Cascade (current D_Full): L0+L1~L4 전체 호출
# Smart Cascade: L0+L1~L3 가 못 잡은 것만 L4 호출
full_true = sum(1 for c in cases if true_by_layers(c, ALL5))
smart_true = l0l3_true + l4_recovered  # L0~L3 잡음 + L4가 추가로 잡음

print("=" * 90)
print("  Phase 3 — B.6 L4 Smart Skip Analysis")
print("=" * 90)

print(f"\n[Case-level breakdown]")
print(f"  L0+L1~L3 이미 neutralize:   {l0l3_true:>5d}  ({100*l0l3_true/total:.2f}%)  → L4 스킵 가능")
print(f"  L0~L3 놓친 → L4 필요:        {l4_needed:>5d}  ({100*l4_needed/total:.2f}%)")
print(f"    └ L4가 복구:              {l4_recovered:>5d}  ({100*l4_recovered/l4_needed:.2f}% of L4-called)")
print(f"    └ L4도 못 잡음:            {l4_missed:>5d}  ({100*l4_missed/l4_needed:.2f}% of L4-called)")

print(f"\n[Throughput / Cost comparison]")
print(f"  Full Cascade (D):    L4 호출 {total:>5d}회  → TRUE {full_true} ({100*full_true/total:.2f}%)")
print(f"  Smart Cascade:       L4 호출 {l4_needed:>5d}회  → TRUE {smart_true} ({100*smart_true/total:.2f}%)")
print(f"\n  ↓ Cost savings: {100*(total-l4_needed)/total:.2f}% fewer L4 calls")
print(f"  ↓ Detection impact: {100*full_true/total - 100*smart_true/total:+.2f}%p (smart vs full)")

# Latency (projected)
L4_AVG_MS = 1542  # from phase1_latency_precise.json, gpt4o-pii-judge mean
total_l4_ms_full = total * L4_AVG_MS
total_l4_ms_smart = l4_needed * L4_AVG_MS
print(f"\n[Latency projection at avg L4 = {L4_AVG_MS}ms]")
print(f"  Full cascade L4 time:   {total_l4_ms_full/1000/60:.1f} min total")
print(f"  Smart cascade L4 time:  {total_l4_ms_smart/1000/60:.1f} min total")
print(f"  Saved:                  {(total_l4_ms_full - total_l4_ms_smart)/1000/60:.1f} min ({100*(1 - l4_needed/total):.2f}%)")

# Per-token cost projection
# gpt-4o-mini ~$0.15 / 1M input tokens, ~$0.60 / 1M output tokens
# Assume ~500 tokens input + 100 tokens output per call
COST_PER_CALL = (500 * 0.15 + 100 * 0.60) / 1_000_000
total_cost_full = total * COST_PER_CALL
total_cost_smart = l4_needed * COST_PER_CALL
print(f"\n[Cost projection at ~${COST_PER_CALL*1000:.3f}/1000 calls]")
print(f"  Full cascade:  ${total_cost_full:.4f} for 10k")
print(f"  Smart cascade: ${total_cost_smart:.4f} for 10k (saved {100*(1 - l4_needed/total):.2f}%)")

result = {
    "total_cases": total,
    "l0l3_neutralized": l0l3_true,
    "l4_needed": l4_needed,
    "l4_recovered": l4_recovered,
    "l4_missed": l4_missed,
    "full_true_rate": round(100 * full_true / total, 2),
    "smart_true_rate": round(100 * smart_true / total, 2),
    "detection_impact_pp": round(100 * full_true / total - 100 * smart_true / total, 4),
    "l4_call_reduction_pct": round(100 * (total - l4_needed) / total, 2),
    "l4_avg_latency_ms": L4_AVG_MS,
    "projected_latency_saved_min": round((total - l4_needed) * L4_AVG_MS / 1000 / 60, 1),
    "projected_cost_saved_usd_10k": round(total_cost_full - total_cost_smart, 6),
}
json.dump(result, open("phase3_l4_smart_skip.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nSaved: phase3_l4_smart_skip.json")
