"""Fig 13 — Layer 0 Ablation visualization: Norm vs Dict vs Full contribution."""
import json
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

mpl.rcParams["font.family"] = "Malgun Gothic"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["savefig.dpi"] = 300

C_BASE = "#999999"
C_N = "#6c757d"  # gray
C_D = "#5cb85c"  # green
C_F = "#337ab7"  # blue

data = json.load(open("phase3_ablation.json", "r", encoding="utf-8"))

slices = ["KR_semantic", "KR_format", "KR_checksum", "KR", "overall", "EN"]
labels = ["KR_semantic\n(text-type)", "KR_format", "KR_checksum", "KR all", "Overall", "English"]

fig, ax = plt.subplots(figsize=(11, 6))

x = np.arange(len(slices))
w = 0.22

base = [data[s]["A_baseline"] for s in slices]
n_gain = [data[s]["N_gain"] for s in slices]
d_gain = [data[s]["D_gain"] for s in slices]
f_gain = [data[s]["F_gain"] for s in slices]

# Stacked gain bars showing contribution decomposition
# For each slice: baseline + N contribution + (D contribution - synergy) + synergy
# Simpler: side-by-side bars for baseline / +N / +D / +Full
baseline_vals = base
n_vals = [b + n for b, n in zip(base, n_gain)]
d_vals = [b + d for b, d in zip(base, d_gain)]
f_vals = [b + f for b, f in zip(base, f_gain)]

ax.bar(x - 1.5*w, baseline_vals, w, label="Baseline (L1~L3)", color=C_BASE, edgecolor="black", linewidth=0.5)
ax.bar(x - 0.5*w, n_vals, w, label="+ Norm only", color=C_N, edgecolor="black", linewidth=0.5)
ax.bar(x + 0.5*w, d_vals, w, label="+ Dict only", color=C_D, edgecolor="black", linewidth=0.5)
ax.bar(x + 1.5*w, f_vals, w, label="+ Full (Norm+Dict)", color=C_F, edgecolor="black", linewidth=0.5)

for i, (b, n, d, f) in enumerate(zip(baseline_vals, n_vals, d_vals, f_vals)):
    ax.text(i - 1.5*w, b + 1, f"{b:.1f}%", ha="center", va="bottom", fontsize=8)
    ax.text(i - 0.5*w, n + 1, f"{n:.1f}%", ha="center", va="bottom", fontsize=8)
    ax.text(i + 0.5*w, d + 1, f"{d:.1f}%", ha="center", va="bottom", fontsize=8)
    ax.text(i + 1.5*w, f + 1, f"{f:.1f}%", ha="center", va="bottom", fontsize=8, fontweight="bold")

# Annotate KR_semantic with decomposition
ks = data["KR_semantic"]
ax.annotate(
    f"Dict가 Layer 0 효과의 96%\n(+{ks['D_gain']}%p / +{ks['F_gain']}%p total)\nNorm 단독: +{ks['N_gain']}%p\nSynergy: +{ks['F_gain']-ks['N_gain']-ks['D_gain']:.2f}%p",
    xy=(0, ks["A_plus_F"]),
    xytext=(0.5, 70),
    fontsize=11,
    ha="left",
    color="darkgreen",
    fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="darkgreen"),
    bbox=dict(boxstyle="round", fc="white", ec="darkgreen", lw=1.5),
)

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=10)
ax.set_ylabel("TRUE detection rate (%)", fontsize=11)
ax.set_title("Fig 13 — Layer 0 Ablation: Norm vs Dict vs Full contribution\n"
             "Dictionary가 Layer 0의 거의 모든 효과를 담당 (KR_semantic: +38.10 / +39.55%p)",
             fontsize=12)
ax.legend(loc="lower right", fontsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.set_ylim(0, 110)
plt.tight_layout()
plt.savefig("fig13_ablation.png", bbox_inches="tight")
plt.close()
print("saved fig13_ablation.png")
