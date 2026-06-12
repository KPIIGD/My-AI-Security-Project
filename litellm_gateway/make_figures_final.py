"""Final 4-way figures from run_e_final_summary.json."""
import json
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from collections import defaultdict
import re

mpl.rcParams["font.family"] = "Malgun Gothic"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["savefig.dpi"] = 300
mpl.rcParams["figure.dpi"] = 120

C_A = "#d9534f"   # red
C_B = "#f0ad4e"   # orange
C_C = "#5cb85c"   # green
C_D = "#337ab7"   # blue

s = json.load(open("run_e_final_summary.json", "r", encoding="utf-8"))
cfgs = ["A_Baseline", "B_Baseline_L4", "C_With_L0", "D_Full"]
cfg_labels = ["A) Baseline\n(L1~L3)", "B) +L4\n(GPT-4o-mini)",
              "C) +L0\n(Korean normalizer)", "D) Full\n(L0+L4)"]
cfg_colors = [C_A, C_B, C_C, C_D]


# Fig 10 — Final 4-way overall bypass across slices
fig, ax = plt.subplots(figsize=(12, 6))
slices = [
    ("Overall", None),
    ("English", ("by_lang", "EN")),
    ("Korean", ("by_lang", "KR")),
    ("KR_checksum", ("by_lang_x_validity", "KR_checksum")),
    ("KR_format", ("by_lang_x_validity", "KR_format")),
    ("KR_semantic\n(text-type PII)", ("by_lang_x_validity", "KR_semantic")),
]
def get_bp(cfg, slice_path):
    if slice_path is None: return s["overall"][cfg]["real_bypass_rate"]
    sec, key = slice_path
    return s[sec][cfg][key]["real_bypass_rate"]

x = np.arange(len(slices))
w = 0.21
for i, cfg in enumerate(cfgs):
    vals = [get_bp(cfg, sp) for _, sp in slices]
    offset = (i - 1.5) * w
    bars = ax.bar(x + offset, vals, w, label=cfg_labels[i].replace("\n", " "),
                  color=cfg_colors[i], edgecolor="black", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.6, f"{v:.1f}",
                ha="center", va="bottom", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels([lab for lab, _ in slices], fontsize=10)
ax.set_ylabel("Real bypass rate (%)", fontsize=11)
ax.set_title("Real bypass rate — 4-way comparison (TRUE detection, 10k)\nC (Layer 0) beats B (LLM judge) in every Korean slice", fontsize=12)
ax.legend(loc="upper left", fontsize=9)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.set_ylim(0, 58)
plt.tight_layout()
plt.savefig("fig10_4way_bypass.png", bbox_inches="tight")
plt.close()
print("saved fig10_4way_bypass.png")


# Fig 11 — KR_semantic 4-way (THE money chart)
fig, ax = plt.subplots(figsize=(9, 6))
ks = s["by_lang_x_validity"]
values = [ks[cfg]["KR_semantic"]["true_rate"] for cfg in cfgs]
bypass = [ks[cfg]["KR_semantic"]["real_bypass_rate"] for cfg in cfgs]

x = np.arange(len(cfgs))
bars = ax.bar(x, values, color=cfg_colors, edgecolor="black", linewidth=0.7, width=0.6)
for bar, t, bp in zip(bars, values, bypass):
    ax.text(bar.get_x() + bar.get_width()/2, t + 1.2, f"{t:.2f}%\n(bypass {bp:.2f}%)",
            ha="center", va="bottom", fontsize=11, fontweight="bold")

# Delta bracket annotations
def bracket(ax, x1, x2, y, label, color):
    ax.annotate("", xy=(x1, y), xytext=(x2, y),
                arrowprops=dict(arrowstyle="-", color=color, lw=1.5))
    ax.text((x1 + x2) / 2, y + 1, label, ha="center", fontsize=10, color=color, fontweight="bold")

top = max(values) + 8
bracket(ax, 1, 2, top, f"C > B: +{values[2]-values[1]:.2f}%p (L0 beats LLM judge)", "darkgreen")

ax.set_xticks(x)
ax.set_xticklabels(cfg_labels, fontsize=10)
ax.set_ylabel("TRUE detection rate (%)", fontsize=11)
ax.set_title(f"KR_semantic (Korean text-type PII, n={ks['A_Baseline']['KR_semantic']['n']}) — 4-way head-to-head\n"
             f"Layer 0 alone beats GPT-4o judge; adding both reaches {values[3]:.2f}%", fontsize=12)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.set_ylim(0, 118)
plt.tight_layout()
plt.savefig("fig11_kr_semantic_4way.png", bbox_inches="tight")
plt.close()
print("saved fig11_kr_semantic_4way.png")


# Fig 12 — Hardest PII 4-way (recompute from raw data for ones not in top20)
def is_pii(p, t):
    if not p or not t: return False
    if p in t: return True
    pd = re.sub(r"\D","",p); td = re.sub(r"\D","",t)
    return len(pd) >= 6 and pd in td

def classify(case, layers):
    pii = case.get("pii_value", "") or case.get("original", "") or ""
    mut = case.get("mutated", "")
    any_t = any_f = False
    for lr in case.get("layer_results", []):
        if lr["layer"] not in layers: continue
        if lr.get("error") or lr.get("action") == "ERROR": continue
        out = lr.get("output", "")
        if out == mut or out == "": continue
        if out == "[BLOCKED]": any_t = True; continue
        if is_pii(pii, out): any_f = True
        else: any_t = True
    if any_t: return "TRUE"
    return "BYPASS"

def bp_rate(cases, layers):
    n = len(cases); b = sum(1 for c in cases if classify(c, layers) != "TRUE")
    return round(100*b/n, 2) if n else 0

files = {
    "A_Baseline": ("eval_10k_l1l3.json", {"Presidio PII","Bedrock Guardrail","Lakera"}),
    "B_Baseline_L4": ("eval_10k_l1l4_full.json", {"Presidio PII","Bedrock Guardrail","Lakera","gpt4o-pii-judge"}),
    "C_With_L0": ("eval_10k_l0_l1l3.json", {"Presidio PII","Bedrock Guardrail","Lakera","korean-layer0"}),
    "D_Full": ("eval_10k_l0_l1l4_full.json", {"Presidio PII","Bedrock Guardrail","Lakera","korean-layer0","gpt4o-pii-judge"}),
}
datasets = {k: json.load(open(f,"r",encoding="utf-8"))["results"] for k, (f, _) in files.items()}

# Top 15 by baseline bypass
base = datasets["A_Baseline"]
by_pii_A = defaultdict(list)
for c in base: by_pii_A[c.get("pii_type")].append(c)
ranked = []
for t, cs in by_pii_A.items():
    if len(cs) >= 30:
        a_bp = bp_rate(cs, files["A_Baseline"][1])
        ranked.append((t, len(cs), a_bp))
ranked.sort(key=lambda x: x[2], reverse=True)
ranked = ranked[:15]

# For each PII, compute bypass under B/C/D using case-id-matched datasets
# Match by id across files — same 10k sample
ids_per_pii = {t: {c.get("id","") for c in cs} for t, cs, _ in [(t, by_pii_A[t], 0) for t, _, _ in ranked]}

rows = []
for t, n, a_bp in ranked:
    ids = {c.get("id","") for c in by_pii_A[t]}
    r = {"pii": t, "n": n, "A": a_bp}
    for key in ["B_Baseline_L4", "C_With_L0", "D_Full"]:
        cs_key = [c for c in datasets[key] if c.get("id","") in ids]
        r[key[0]] = bp_rate(cs_key, files[key][1])
    rows.append(r)

fig, ax = plt.subplots(figsize=(12, 8))
piis = [r["pii"] for r in rows]
y = np.arange(len(piis))
h = 0.2
ax.barh(y - 1.5*h, [r["A"] for r in rows], h, label="A) Baseline", color=C_A, edgecolor="black", linewidth=0.4)
ax.barh(y - 0.5*h, [r["B"] for r in rows], h, label="B) +L4", color=C_B, edgecolor="black", linewidth=0.4)
ax.barh(y + 0.5*h, [r["C"] for r in rows], h, label="C) +L0", color=C_C, edgecolor="black", linewidth=0.4)
ax.barh(y + 1.5*h, [r["D"] for r in rows], h, label="D) Full", color=C_D, edgecolor="black", linewidth=0.4)
ax.set_yticks(y)
ax.set_yticklabels(piis, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel("Real bypass rate (%)", fontsize=11)
ax.set_title("Top 15 hardest PII — 4-way bypass rate", fontsize=12)
ax.legend(loc="lower right", fontsize=10)
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.set_xlim(0, 105)
for i, r in enumerate(rows):
    for j, (k, off) in enumerate(zip(["A","B","C","D"], [-1.5,-0.5,0.5,1.5])):
        v = r[k]
        ax.text(v + 0.7, i + off*h, f"{v:.0f}%", va="center", fontsize=7)
plt.tight_layout()
plt.savefig("fig12_hardest_pii_4way.png", bbox_inches="tight")
plt.close()
print("saved fig12_hardest_pii_4way.png")

print("\nAll final figures saved (fig10~fig12).")
