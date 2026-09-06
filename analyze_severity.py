#!/usr/bin/env python3
"""Locked analysis for the V3 confirmatory severity run.
Implements SEVERITY_ANALYSIS_LOCK.md EXACTLY. numpy only. Reads immutable raw;
writes results/analysis/severity_analysis.json. Does not modify raw.
"""
import os, sys, json, glob
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
RUN = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(f"{ROOT}/results/raw/severity_run_*"))[-1]
recs = json.load(open(f"{RUN}/severity.json"))
SIG = [0.10, 0.20, 0.40, 0.60, 0.80, 1.00]
CONDS = ["behavioural", "architectural"]
SEEDS = sorted({r["seed"] for r in recs})
T49 = 2.009575  # t_{.975, df=49}

# index: delta[(seed,cond,sigma)] and q_ref_abrupt[(seed,sigma)], ref traj
D = {}
QREF = {}
REFTRAJ = {}
for r in recs:
    if r["truth_regime"] == "partial_shift":
        if r["condition"] in CONDS:
            D[(r["seed"], r["condition"], r["sigma"])] = r["delta_adapt"]
        if r["condition"] == "reference":
            QREF[(r["seed"], r["sigma"])] = r["q_ref_abrupt"]
            REFTRAJ[(r["seed"], r["sigma"])] = r["quality_trajectory"]

def ci95(x):
    x = np.asarray(x, float); m = x.mean(); se = x.std(ddof=1)/np.sqrt(len(x))
    return float(m), float(m - T49*se), float(m + T49*se), float(x.std(ddof=1))

# ---- PRIMARY: per-seed OLS slope of Delta_adapt on sigma ---------------------
sig = np.array(SIG)
def slope(ys):
    ys = np.asarray(ys, float)
    A = np.vstack([sig, np.ones_like(sig)]).T
    b = np.linalg.lstsq(A, ys, rcond=None)[0][0]
    return float(b)

beta = {c: [] for c in CONDS}
for s in SEEDS:
    for c in CONDS:
        beta[c].append(slope([D[(s, c, x)] for x in SIG]))
beta = {c: np.array(v) for c, v in beta.items()}

beta_bar = (beta["behavioural"] + beta["architectural"]) / 2.0    # avg severity slope per seed
d_seed = beta["architectural"] - beta["behavioural"]              # channel difference per seed

C1 = ci95(beta_bar)      # sigma term (severity dependence)
C2 = ci95(d_seed)        # sigma:condition (channel difference)

# ---- DESCRIPTIVE: per-sigma paired Delta, CI, Cohen d, direction ------------
per_sigma = {}
for c in CONDS:
    per_sigma[c] = {}
    for x in SIG:
        vals = np.array([D[(s, c, x)] for s in SEEDS])
        m, lo, hi, sd = ci95(vals)
        dcoh = m / sd if sd > 0 else float("nan")
        dirpos = float(np.mean(vals > 0))
        per_sigma[c][x] = {"mean": m, "ci_lo": lo, "ci_hi": hi, "cohen_d": dcoh,
                            "frac_positive": dirpos}

# q_ref_abrupt(sigma) descriptive control
qref_curve = {x: float(np.mean([QREF[(s, x)] for s in SEEDS])) for x in SIG}

# ---- Spearman (two-sided) with deterministic permutation --------------------
def spearman(xv, yv):
    xr = np.argsort(np.argsort(xv)); yr = np.argsort(np.argsort(yv))
    xr = xr - xr.mean(); yr = yr - yr.mean()
    return float((xr*yr).sum() / np.sqrt((xr**2).sum()*(yr**2).sum()))
rng = np.random.default_rng(20260823)
spear = {}
for c in CONDS:
    xs = np.array([x for s in SEEDS for x in SIG])
    ys = np.array([D[(s, c, x)] for s in SEEDS for x in SIG])
    rho = spearman(xs, ys)
    perm = np.array([abs(spearman(xs, rng.permutation(ys))) for _ in range(10000)])
    p = float(np.mean(perm >= abs(rho)))
    spear[c] = {"rho": rho, "perm_p_two_sided": p}

# ---- normalized ratio (exploratory, sigma>=0.20) ----------------------------
ratio = {}
for c in CONDS:
    ratio[c] = {}
    for x in SIG:
        if x < 0.20: continue
        rr = []
        for s in SEEDS:
            traj = REFTRAJ[(s, x)]
            rec_recov = traj[-1] - traj[14]   # q@40 - q@15 (post-shift recovery magnitude)
            if rec_recov > 1e-6:
                rr.append(D[(s, c, x)] / rec_recov)
        ratio[c][x] = float(np.mean(rr)) if rr else None

# ---- anchors ----------------------------------------------------------------
anchor_sigma1 = {c: per_sigma[c][1.00]["mean"] for c in CONDS}
C1_REFERENCE_ADAPT_SPECIFIC = 0.30   # frozen C1 (~0.29-0.32); convergent check, not bit-exact

out = {
    "run_dir": os.path.basename(RUN), "n_records": len(recs), "seeds": len(SEEDS),
    "primary": {
        "sigma_term_avg_slope": {"mean": C1[0], "ci95": [C1[1], C1[2]], "sd": C1[3]},
        "sigma_x_condition_slope_diff_arch_minus_beh": {"mean": C2[0], "ci95": [C2[1], C2[2]], "sd": C2[3]},
        "per_condition_mean_slope": {c: float(beta[c].mean()) for c in CONDS},
    },
    "descriptive": {"per_sigma": per_sigma, "q_ref_abrupt_curve": qref_curve,
                    "spearman": spear, "normalized_ratio_expl": ratio},
    "anchors": {"sigma0_delta": 0.0, "sigma1_mean_delta": anchor_sigma1,
                "C1_convergent_reference": C1_REFERENCE_ADAPT_SPECIFIC},
}
os.makedirs(f"{ROOT}/results/analysis", exist_ok=True)
json.dump(out, open(f"{ROOT}/results/analysis/severity_analysis.json", "w"), indent=2)

# ---- console summary --------------------------------------------------------
print("PRIMARY (confirmatory):")
print(f"  sigma term (avg severity slope):  mean={C1[0]:+.4f}  95% CI [{C1[1]:+.4f}, {C1[2]:+.4f}]")
print(f"  sigma:condition (arch - beh slope): mean={C2[0]:+.4f}  95% CI [{C2[1]:+.4f}, {C2[2]:+.4f}]")
print(f"  per-condition mean slope: beh={beta['behavioural'].mean():+.4f}  arch={beta['architectural'].mean():+.4f}")
print("\nDESCRIPTIVE per-sigma mean Delta_adapt (95% CI) [dir%]:")
for c in CONDS:
    print(f"  {c}:")
    for x in SIG:
        d = per_sigma[c][x]
        print(f"    s={x:.2f}  {d['mean']:+.3f}  [{d['ci_lo']:+.3f},{d['ci_hi']:+.3f}]  d={d['cohen_d']:+.2f}  dir={d['frac_positive']*100:.0f}%")
print("\nq_ref_abrupt(sigma):  " + "  ".join(f"{x:.2f}:{qref_curve[x]:.3f}" for x in SIG))
print(f"\nSpearman rho (perm p): " + "  ".join(f"{c}:{spear[c]['rho']:+.3f}(p={spear[c]['perm_p_two_sided']:.4f})" for c in CONDS))
print(f"\nAnchor sigma=1 mean Delta: beh={anchor_sigma1['behavioural']:.3f} arch={anchor_sigma1['architectural']:.3f}  (C1 convergent ~0.30)")
print("analysis -> results/analysis/severity_analysis.json")
