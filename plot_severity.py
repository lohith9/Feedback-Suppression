#!/usr/bin/env python3
"""Primary figure: Delta_adapt vs sigma (both channels, 95% CI), with sigma=0/1
markers and the C1 convergent reference band. Descriptive; does not imply that
cell-wise significance is the primary result."""
import os, sys, json, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(f"{ROOT}/results/analysis/severity_analysis.json"))
SIG = [0.10, 0.20, 0.40, 0.60, 0.80, 1.00]
ps = A["descriptive"]["per_sigma"]

fig, ax = plt.subplots(figsize=(5.2, 3.6))
# C1 convergent reference band (~0.30 at full inversion)
ax.axhspan(0.29, 0.32, color="#cccccc", alpha=0.5, label="C1 reference band (~0.30, σ=1)")
colors = {"behavioural": "#c0392b", "architectural": "#2b6ca3"}
labels = {"behavioural": "Factor A (producer deference)", "architectural": "Factor B (readable write-back)"}
def cell(c, x):
    d = ps[c]
    return d[str(x)] if str(x) in d else d[x]
for c in ["behavioural", "architectural"]:
    xs = [0.0] + SIG
    ys = [0.0] + [cell(c, x)["mean"] for x in SIG]
    los = [0.0] + [cell(c, x)["ci_lo"] for x in SIG]
    his = [0.0] + [cell(c, x)["ci_hi"] for x in SIG]
    yerr = [np.array(ys) - np.array(los), np.array(his) - np.array(ys)]
    ax.errorbar(xs, ys, yerr=yerr, marker="o", ms=4, lw=1.6, capsize=3,
                color=colors[c], label=labels[c])
ax.axvline(0.0, color="#888", ls=":", lw=0.8)
ax.axvline(1.0, color="#888", ls=":", lw=0.8)
ax.annotate("σ=0: Δ≡0\n(by construction)", xy=(0.0, 0.0), xytext=(0.06, 0.11),
            fontsize=7, color="#444")
ax.set_xlabel("shift severity  σ  (fraction of entities whose truth flips)")
ax.set_ylabel("adaptation-specific penalty  Δ_adapt  (95% CI)")
ax.set_title("Severity-response of the structured-state feedback effect\n(controlled synthetic; 50 seeds; descriptive)", fontsize=9)
ax.set_xlim(-0.03, 1.05); ax.set_ylim(-0.02, 0.38)
ax.legend(fontsize=7, loc="upper left", framealpha=0.9)
ax.grid(alpha=0.25)
fig.tight_layout()
os.makedirs(f"{ROOT}/results/figures/severity", exist_ok=True)
fig.savefig(f"{ROOT}/results/figures/severity/fig_delta_vs_sigma.pdf")
fig.savefig("/tmp/fig_delta_vs_sigma.png", dpi=150)
print("figure -> results/figures/severity/fig_delta_vs_sigma.pdf")
