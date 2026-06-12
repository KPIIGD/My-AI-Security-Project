"""
Generate paper-ready figures from run_c_l0_summary.json + analyze_l0_deep.json.

Output PNGs (300dpi):
  fig1_overall_bypass.png        — Overall bypass rate baseline vs L0
  fig2_lang_x_validity.png        — Lang × Validity grouped bar (TRUE rate before/after)
  fig3_hardest_pii.png            — Top 20 hardest PII bypass before/after
  fig4_mutation_level.png         — Per mutation level recovery
  fig5_l0_solo_pii.png            — L0 solo catches by PII type
"""
import json
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# Korean font
mpl.rcParams["font.family"] = "Malgun Gothic"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["savefig.dpi"] = 300
mpl.rcParams["figure.dpi"] = 120

C_BASE = "#d9534f"  # red — bypass / vulnerability
C_L0 = "#5cb85c"    # green — L0 effect
C_NEUTRAL = "#999999"

summary = json.load(open("run_c_l0_summary.json", "r", encoding="utf-8"))
deep = json.load(open("analyze_l0_deep.json", "r", encoding="utf-8"))


# ─────────────────────────────────────────────
# Fig 1 — Overall bypass rate, with breakdown by lang/validity slices
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5.5))

slices = [
    ("Overall (10k)",
     summary["baseline_overall"]["real_bypass_rate"],
     summary["with_l0_overall"]["real_bypass_rate"]),
    ("English",
     summary["baseline_by_lang"]["EN"]["real_bypass_rate"],
     summary["with_l0_by_lang"]["EN"]["real_bypass_rate"]),
    ("Korean",
     summary["baseline_by_lang"]["KR"]["real_bypass_rate"],
     summary["with_l0_by_lang"]["KR"]["real_bypass_rate"]),
    ("KR_checksum",
     summary["baseline_by_lang_x_validity"]["KR_checksum"]["real_bypass_rate"],
     summary["with_l0_by_lang_x_validity"]["KR_checksum"]["real_bypass_rate"]),
    ("KR_format",
     summary["baseline_by_lang_x_validity"]["KR_format"]["real_bypass_rate"],
     summary["with_l0_by_lang_x_validity"]["KR_format"]["real_bypass_rate"]),
    ("KR_semantic\n(text-type PII)",
     summary["baseline_by_lang_x_validity"]["KR_semantic"]["real_bypass_rate"],
     summary["with_l0_by_lang_x_validity"]["KR_semantic"]["real_bypass_rate"]),
]

x = np.arange(len(slices))
w = 0.36
base_vals = [s[1] for s in slices]
l0_vals = [s[2] for s in slices]

b1 = ax.bar(x - w/2, base_vals, w, label="Baseline (L1~L3)", color=C_BASE, edgecolor="black", linewidth=0.5)
b2 = ax.bar(x + w/2, l0_vals, w, label="With Layer 0 (L0~L3)", color=C_L0, edgecolor="black", linewidth=0.5)

for i, (b, v) in enumerate(zip(b1, base_vals)):
    ax.text(b.get_x() + w/2, v + 1, f"{v:.1f}%", ha="center", va="bottom", fontsize=9, color=C_BASE, fontweight="bold")
for i, (b, v) in enumerate(zip(b2, l0_vals)):
    ax.text(b.get_x() + w/2, v + 1, f"{v:.1f}%", ha="center", va="bottom", fontsize=9, color=C_L0, fontweight="bold")
    delta = l0_vals[i] - base_vals[i]
    ax.annotate(f"{delta:+.1f}p", xy=(i, max(base_vals[i], l0_vals[i]) + 5),
                ha="center", fontsize=8, color="#333")

ax.set_xticks(x)
ax.set_xticklabels([s[0] for s in slices], fontsize=10)
ax.set_ylabel("Real bypass rate (%)", fontsize=11)
ax.set_title("Real bypass rate — Baseline vs With Layer 0 (TRUE detection, 10k stratified)", fontsize=12)
ax.legend(loc="upper left", fontsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.set_ylim(0, 65)
plt.tight_layout()
plt.savefig("fig1_overall_bypass.png", bbox_inches="tight")
plt.close()
print("saved fig1_overall_bypass.png")


# ─────────────────────────────────────────────
# Fig 2 — Lang × Validity TRUE detection rate (clearer angle)
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5.5))

buckets = ["EN_format", "EN_checksum", "KR_checksum", "KR_format", "KR_semantic"]
labels = ["EN format", "EN checksum", "KR checksum", "KR format", "KR semantic"]
base_t = [summary["baseline_by_lang_x_validity"][b]["true_rate"] for b in buckets]
l0_t = [summary["with_l0_by_lang_x_validity"][b]["true_rate"] for b in buckets]

x = np.arange(len(buckets))
w = 0.36
b1 = ax.bar(x - w/2, base_t, w, label="Baseline", color=C_BASE, edgecolor="black", linewidth=0.5)
b2 = ax.bar(x + w/2, l0_t, w, label="With Layer 0", color=C_L0, edgecolor="black", linewidth=0.5)

for i, v in enumerate(base_t):
    ax.text(i - w/2, v + 1, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
for i, v in enumerate(l0_t):
    ax.text(i + w/2, v + 1, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
    d = l0_t[i] - base_t[i]
    if d > 0.5:
        ax.annotate(f"+{d:.1f}p", xy=(i, max(base_t[i], l0_t[i]) + 6),
                    ha="center", fontsize=9, color="darkgreen", fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=10)
ax.set_ylabel("TRUE detection rate (%)", fontsize=11)
ax.set_title("TRUE detection rate by Language × Validity group", fontsize=12)
ax.legend(loc="lower right", fontsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.set_ylim(0, 115)
plt.tight_layout()
plt.savefig("fig2_lang_x_validity.png", bbox_inches="tight")
plt.close()
print("saved fig2_lang_x_validity.png")


# ─────────────────────────────────────────────
# Fig 3 — Hardest PII top 20 — bypass before/after
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 8))

hard = summary["baseline_hardest_pii"][:20]
pii_types = [r["pii_type"] for r in hard]
base_bp = [r["real_bypass_rate"] for r in hard]

# Find L0 bypass for same types
l0_map = {r["pii_type"]: r["real_bypass_rate"]
          for r in summary["with_l0_hardest_pii"]}
# Fallback: recompute from full data if missing in top25
l0_cases = json.load(open("eval_10k_l0_l1l3.json", "r", encoding="utf-8"))["results"]
import re
def is_pii(p, t):
    if not p or not t: return False
    if p in t: return True
    pd = re.sub(r"\D", "", p); td = re.sub(r"\D", "", t)
    return len(pd) >= 6 and pd in td
def true_rate_for(pii_type, layers_set):
    sub = [c for c in l0_cases if c.get("pii_type") == pii_type]
    if not sub: return None
    total, true_n = len(sub), 0
    for c in sub:
        pii = c.get("pii_value", "") or c.get("original", "")
        mut = c.get("mutated", "")
        for lr in c.get("layer_results", []):
            if lr["layer"] not in layers_set: continue
            out = lr.get("output", "")
            if out == "[BLOCKED]":
                true_n += 1; break
            if out and out != mut and not is_pii(pii, out):
                true_n += 1; break
    return round(100 * (total - true_n) / total, 2)

ALL4 = {"korean-layer0", "Presidio PII", "Bedrock Guardrail", "Lakera"}
l0_bp = []
for t in pii_types:
    if t in l0_map:
        l0_bp.append(l0_map[t])
    else:
        v = true_rate_for(t, ALL4)
        l0_bp.append(v if v is not None else 0)

y = np.arange(len(pii_types))
h = 0.4
b1 = ax.barh(y - h/2, base_bp, h, label="Baseline (L1~L3)", color=C_BASE, edgecolor="black", linewidth=0.5)
b2 = ax.barh(y + h/2, l0_bp, h, label="With Layer 0 (L0~L3)", color=C_L0, edgecolor="black", linewidth=0.5)
ax.set_yticks(y)
ax.set_yticklabels(pii_types, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel("Real bypass rate (%)", fontsize=11)
ax.set_title("Top 20 hardest PII types — bypass rate before/after Layer 0", fontsize=12)
ax.legend(loc="lower right", fontsize=10)
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.set_xlim(0, 105)

for i, v in enumerate(base_bp):
    ax.text(v + 0.5, i - h/2, f"{v:.0f}%", va="center", fontsize=8)
for i, v in enumerate(l0_bp):
    label = f"{v:.0f}%" if v > 0 else "0%"
    ax.text(v + 0.5, i + h/2, label, va="center", fontsize=8, color="darkgreen" if v < base_bp[i] - 30 else "black")

plt.tight_layout()
plt.savefig("fig3_hardest_pii.png", bbox_inches="tight")
plt.close()
print("saved fig3_hardest_pii.png")


# ─────────────────────────────────────────────
# Fig 4 — Per mutation level recovery
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))

levels = sorted(summary["baseline_by_mutation_level"].keys(), key=lambda k: int(k))
level_names = ["L0 Original", "L1 Character", "L2 Encoding", "L3 Format", "L4 Linguistic", "L5 Context"]
base_bp = [summary["baseline_by_mutation_level"][lv]["real_bypass_rate"] for lv in levels]
l0_bp = [summary["with_l0_by_mutation_level"][lv]["real_bypass_rate"] for lv in levels]

x = np.arange(len(levels))
w = 0.36
b1 = ax.bar(x - w/2, base_bp, w, label="Baseline", color=C_BASE, edgecolor="black", linewidth=0.5)
b2 = ax.bar(x + w/2, l0_bp, w, label="With Layer 0", color=C_L0, edgecolor="black", linewidth=0.5)

for i, v in enumerate(base_bp):
    ax.text(i - w/2, v + 0.4, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
for i, v in enumerate(l0_bp):
    ax.text(i + w/2, v + 0.4, f"{v:.1f}", ha="center", va="bottom", fontsize=9)

ax.set_xticks(x)
ax.set_xticklabels(level_names, fontsize=10)
ax.set_ylabel("Real bypass rate (%)", fontsize=11)
ax.set_title("Bypass rate by mutation level", fontsize=12)
ax.legend(loc="upper right", fontsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.set_ylim(0, max(base_bp) + 8)
plt.tight_layout()
plt.savefig("fig4_mutation_level.png", bbox_inches="tight")
plt.close()
print("saved fig4_mutation_level.png")


# ─────────────────────────────────────────────
# Fig 5 — L0 solo catches by PII type (top 20)
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 7))

solo = list(deep["l0_solo_by_pii"].items())[:20]
piis = [k for k, _ in solo]
counts = [v for _, v in solo]

y = np.arange(len(piis))
ax.barh(y, counts, color=C_L0, edgecolor="black", linewidth=0.5)
ax.set_yticks(y)
ax.set_yticklabels(piis, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel("L0 solo catches (cases the others all missed)", fontsize=11)
ax.set_title(f"Layer 0 solo catches by PII type — {sum(counts)} of {sum(deep['l0_solo_by_pii'].values())} total", fontsize=12)
ax.grid(axis="x", linestyle="--", alpha=0.4)
for i, v in enumerate(counts):
    ax.text(v + 1, i, str(v), va="center", fontsize=9)

plt.tight_layout()
plt.savefig("fig5_l0_solo_pii.png", bbox_inches="tight")
plt.close()
print("saved fig5_l0_solo_pii.png")

print("\nAll 5 figures saved.")
