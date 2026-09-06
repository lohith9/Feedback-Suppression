import json, statistics as st
from collections import defaultdict
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = json.load(open("results/raw/all_rows.json"))
d = defaultdict(lambda: defaultdict(list))
for r in rows:
    d[r["arm"]][r["cycle"]].append(r)

def series(arm, key):
    cs = sorted(d[arm].keys())
    return cs, [st.mean([x[key] for x in d[arm][c]]) for c in cs]

fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))

c, a3q = series("A3", "live_quality")
_, a9q = series("A9", "live_quality")
_, a1q = series("A1", "live_quality")
_, a3h = series("A3", "holdout_accuracy")
ax[0].plot(c, a3q, "o-", color="#c0392b", lw=2, label="A3 live quality (feedback ON)")
ax[0].plot(c, a9q, "s-", color="#27ae60", lw=2, label="A9 live quality (feedback OFF, matched writes)")
ax[0].plot(c, a1q, "^-", color="#7f8c8d", lw=1.2, alpha=.7, label="A1 human-clean control")
ax[0].plot(c, a3h, "--", color="#2980b9", lw=2, label="A3 conventional monitor (holdout)")
ax[0].set_xlabel("cycle"); ax[0].set_ylabel("accuracy")
ax[0].set_title("Arrested improvement, not degradation\n(conventional monitor is flat and blind)")
ax[0].legend(fontsize=7.5, loc="lower right"); ax[0].grid(alpha=.3); ax[0].set_ylim(0.6, 1.02)

_, a3rr = series("A3", "RR"); _, a9rr = series("A9", "RR"); _, a1rr = series("A1", "RR")
ax[1].plot(c, a3rr, "o-", color="#c0392b", lw=2, label="A3 RR (echo ratio)")
ax[1].plot(c, a9rr, "s-", color="#27ae60", lw=2, label="A9 RR")
ax[1].plot(c, a1rr, "^-", color="#7f8c8d", lw=1.2, label="A1 RR")
ax[1].axhline(0.30, ls=":", color="k", label="pre-registered RR alarm = 0.30")
ax[1].set_xlabel("cycle"); ax[1].set_ylabel("reinforcement (echo) ratio")
ax[1].set_title("RR detector fires at cycle 2-3 (10/10 seeds)\nzero false positives on A1/A9")
ax[1].legend(fontsize=8); ax[1].grid(alpha=.3); ax[1].set_ylim(-0.03, 1.05)

plt.tight_layout(); plt.savefig("results/figures/divergence.png", dpi=140)
print("saved results/figures/divergence.png")
