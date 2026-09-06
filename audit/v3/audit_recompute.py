#!/usr/bin/env python3
"""Independent V3 audit — recompute EVERYTHING from raw severity.json.
Does NOT import analyze_severity or trust severity_analysis.json.
numpy only. Read-only on all frozen artifacts.
"""
import os, sys, json, glob, hashlib
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUN = f"{ROOT}/results/raw/severity_run_20260829_190638"
recs = json.load(open(f"{RUN}/severity.json"))
SIG = [0.10, 0.20, 0.40, 0.60, 0.80, 1.00]
CONDS = ["behavioural", "architectural"]
ALLC = ["reference", "behavioural", "architectural"]
SEEDS = sorted({r["seed"] for r in recs})
T49 = 2.0095752344       # t_{.975,49}
report = {}

# ============ STEP 1 — completeness / integrity ============
def qfinal(r): return r["quality_trajectory"][-1]   # cycle 40, independent of stored q_final
prereg_sha = hashlib.sha256(open(f"{ROOT}/preregistration/SHIFT_SEVERITY_V3.yaml","rb").read()).hexdigest()
s1 = {}
s1["n_records"] = len(recs)
s1["n_seeds"] = len(SEEDS)
s1["conditions"] = sorted({r["condition"] for r in recs})
s1["sigmas_present"] = sorted({r["sigma"] for r in recs})
# static once per seed x cond ; abrupt per nonzero sigma x seed x cond
static = {(r["seed"], r["condition"]) for r in recs if r["truth_regime"] == "static"}
abrupt = {(r["seed"], r["condition"], r["sigma"]) for r in recs if r["truth_regime"] == "partial_shift"}
s1["static_cells"] = len(static)                 # expect 150
s1["abrupt_cells"] = len(abrupt)                 # expect 900
s1["static_complete"] = (static == {(s, c) for s in SEEDS for c in ALLC})
s1["abrupt_complete"] = (abrupt == {(s, c, x) for s in SEEDS for c in ALLC for x in SIG})
# duplicates
keys = [(r["seed"], r["condition"], r["sigma"], r["truth_regime"]) for r in recs]
s1["duplicate_records"] = len(keys) - len(set(keys))
# per-record invariants
bad_sigma = [r for r in recs if abs(r["sigma_measured"] - r["sigma"]) > 1e-12]
bad_k = [r for r in recs if r["k"] != round(r["sigma"] * 50)]
bad_prev = [r for r in recs if r["truth_regime"] == "partial_shift"
            and (abs(r["pre_shift_prevalence"] - 0.5) > 1e-12 or abs(r["post_shift_prevalence"] - 0.5) > 1e-12)]
bad_sha = [r for r in recs if r.get("prereg_sha256") != prereg_sha]
bad_ver = [r for r in recs if r.get("code_version") != "severity-v3.0.0"]
s1["measured_eq_declared_sigma"] = (len(bad_sigma) == 0)
s1["k_correct"] = (len(bad_k) == 0)
s1["prevalence_exact_0.5"] = (len(bad_prev) == 0)
s1["prereg_sha_on_all"] = (len(bad_sha) == 0)
s1["code_version_on_all"] = (len(bad_ver) == 0)
s1["prereg_sha_matches_frozen"] = (prereg_sha == "2301d9485133669e411e203d3a66e0719933d97b824c0d4d3ad55957f3a8504b")
# write-volume matched: reference (wb F) vs architectural (wb T) at w=0, per (seed,sigma/static)
wv_ok = True
bykey = {(r["seed"], r["condition"], r["sigma"], r["truth_regime"]): r for r in recs}
for s in SEEDS:
    for reg, xs in (("static", [0.0]), ("partial_shift", SIG)):
        for x in xs:
            rr = bykey.get((s, "reference", x if reg=="partial_shift" else 0.0, reg))
            ra = bykey.get((s, "architectural", x if reg=="partial_shift" else 0.0, reg))
            if rr and ra and rr["writes"] != ra["writes"]:
                wv_ok = False
s1["write_volume_matched"] = wv_ok
report["step1_completeness"] = s1

# ============ STEP 2 — re-derive estimand from raw q (trajectory[-1]) ============
qmap = {}
for r in recs:
    qmap[(r["seed"], r["condition"], r["sigma"], r["truth_regime"])] = qfinal(r)
Draw = {}       # independent Delta_adapt
maxerr = 0.0; mism = 0
for s in SEEDS:
    qrs = qmap[(s, "reference", 0.0, "static")]
    for c in CONDS:
        gs = qrs - qmap[(s, c, 0.0, "static")]
        for x in SIG:
            qra = qmap[(s, "reference", x, "partial_shift")]
            ga = qra - qmap[(s, c, x, "partial_shift")]
            d = ga - gs
            Draw[(s, c, x)] = d
            stored = bykey[(s, c, x, "partial_shift")]["delta_adapt"]
            e = abs(d - stored); maxerr = max(maxerr, e)
            if e > 1e-9: mism += 1
report["step2_estimand"] = {"recomputed_from_raw_trajectory": True,
                            "max_abs_error_vs_stored": maxerr, "mismatched_rows": mism,
                            "n_delta_values": len(Draw)}

# ============ STEP 3 — independent descriptives ============
def ci(x):
    x = np.asarray(x, float); m = x.mean(); sd = x.std(ddof=1); se = sd/np.sqrt(len(x))
    return dict(mean=float(m), sd=float(sd), ci_lo=float(m-T49*se), ci_hi=float(m+T49*se),
                cohen_d=float(m/sd) if sd>0 else None, median=float(np.median(x)),
                min=float(x.min()), max=float(x.max()), frac_pos=float(np.mean(x>0)))
desc = {c: {x: ci([Draw[(s,c,x)] for s in SEEDS]) for x in SIG} for c in CONDS}
# reference / feedback adaptation rates + censored
def adrate(cond, reg, x):
    rs = [bykey[(s, cond, x, reg)] for s in SEEDS]
    return sum(1 for r in rs if r["adapted"]), sum(1 for r in rs if not r["adapted"])
adapt = {}
for x in SIG:
    adapt[x] = {c: adrate(c, "partial_shift", x) for c in ALLC}
adapt["static"] = {c: adrate(c, "static", 0.0) for c in ALLC}
qref = {x: float(np.mean([qmap[(s,"reference",x,"partial_shift")] for s in SEEDS])) for x in SIG}
report["step3_descriptives"] = {"per_sigma": desc, "adaptation_adapted_censored": adapt,
                                "q_ref_abrupt": qref}

# ============ STEP 5 — CI via explicit matrix algebra (per-seed OLS) ============
X = np.vstack([np.array(SIG), np.ones(len(SIG))]).T          # design for slope+intercept
XtXinv = np.linalg.inv(X.T @ X)
def ols_slope(y):
    beta = XtXinv @ X.T @ np.asarray(y, float)
    return float(beta[0])
beta = {c: np.array([ols_slope([Draw[(s,c,x)] for x in SIG]) for s in SEEDS]) for c in CONDS}
beta_bar = (beta["behavioural"] + beta["architectural"]) / 2.0
dslope = beta["architectural"] - beta["behavioural"]
def slope_ci(v):
    v=np.asarray(v,float); m=v.mean(); sd=v.std(ddof=1); se=sd/np.sqrt(len(v))
    return dict(mean=float(m), se=float(se), t=T49, ci_lo=float(m-T49*se), ci_hi=float(m+T49*se), sd=float(sd))
report["step5_primary_CI_matrix"] = {
    "sigma_term_avg_slope": slope_ci(beta_bar),
    "sigma_x_condition_diff": slope_ci(dslope),
    "per_condition_mean_slope": {c: float(beta[c].mean()) for c in CONDS},
    "formula": "per-seed b=(X'X)^-1 X'y on 6 sigma; mean over 50 seeds; SE=sd/sqrt(50); t=2.00958"}

# ============ STEP 6 — linearity / curvature (descriptive) ============
def curve_audit(c):
    mu = np.array([desc[c][x]["mean"] for x in SIG]); xg = np.array(SIG)
    # linear fit
    A = np.vstack([xg, np.ones_like(xg)]).T
    bl = np.linalg.lstsq(A, mu, rcond=None)[0]; res_lin = mu - A@bl
    ss_lin = float((res_lin**2).sum())
    # quadratic fit
    A2 = np.vstack([xg**2, xg, np.ones_like(xg)]).T
    bq = np.linalg.lstsq(A2, mu, rcond=None)[0]; res_q = mu - A2@bq
    ss_q = float((res_q**2).sum())
    sst = float(((mu-mu.mean())**2).sum())
    return dict(means=[float(v) for v in mu], linear_slope=float(bl[0]), linear_intercept=float(bl[1]),
                R2_linear=float(1-ss_lin/sst), quad_coef=float(bq[0]), R2_quad=float(1-ss_q/sst),
                max_abs_resid_linear=float(np.max(np.abs(res_lin))),
                ss_resid_linear=ss_lin, ss_resid_quad=ss_q)
report["step6_shape"] = {c: curve_audit(c) for c in CONDS}

# ============ STEP 7 — channel difference (paired, per sigma + slope) ============
chan = {}
for x in SIG:
    diff = np.array([Draw[(s,"architectural",x)] - Draw[(s,"behavioural",x)] for s in SEEDS])
    chan[x] = ci(diff)
report["step7_channel_diff"] = {"per_sigma_arch_minus_beh": chan,
                                "slope_diff": slope_ci(dslope)}

# ============ STEP 12 — robustness (non-confirmatory) ============
rng = np.random.default_rng(20260829)
# (1) pooled OLS Delta ~ sigma (ignoring clustering) — different path
allx = np.array([x for s in SEEDS for c in CONDS for x in SIG])
ally = np.array([Draw[(s,c,x)] for s in SEEDS for c in CONDS for x in SIG])
Ap = np.vstack([allx, np.ones_like(allx)]).T
bp = np.linalg.lstsq(Ap, ally, rcond=None)[0]
# (2) bootstrap over seeds for avg slope
boot = []
for _ in range(10000):
    idx = rng.integers(0, len(SEEDS), len(SEEDS))
    boot.append(beta_bar[idx].mean())
boot = np.sort(boot)
# (3) leave-one-seed-out on avg slope
loo = [np.delete(beta_bar, i).mean() for i in range(len(SEEDS))]
# (4) Spearman pooled (per condition)
def spear(xv, yv):
    xr=np.argsort(np.argsort(xv)).astype(float); yr=np.argsort(np.argsort(yv)).astype(float)
    xr-=xr.mean(); yr-=yr.mean()
    return float((xr*yr).sum()/np.sqrt((xr**2).sum()*(yr**2).sum()))
sp = {c: spear(np.array([x for s in SEEDS for x in SIG]),
               np.array([Draw[(s,c,x)] for s in SEEDS for x in SIG])) for c in CONDS}
# (5) channel-diff bootstrap
bootd = []
for _ in range(10000):
    idx = rng.integers(0, len(SEEDS), len(SEEDS))
    bootd.append(dslope[idx].mean())
bootd = np.sort(bootd)
report["step12_robustness"] = {
    "pooled_ols_slope_ignoring_clusters": float(bp[0]),
    "bootstrap_avg_slope_ci95": [float(boot[250]), float(boot[9750])],
    "loo_avg_slope_min_max": [float(min(loo)), float(max(loo))],
    "spearman_pooled": sp,
    "channel_diff_bootstrap_ci95": [float(bootd[250]), float(bootd[9750])],
}

# ============ STEP 13 — precision ============
se_bar = float(beta_bar.std(ddof=1)/np.sqrt(len(SEEDS)))
mdes = 2*T49*se_bar   # ~ smallest slope whose CI would exclude 0 given this SE (2*half-width heuristic)
persig_se = {x: float(np.std([Draw[(s,'behavioural',x)] for s in SEEDS], ddof=1)/np.sqrt(50)) for x in SIG}
report["step13_precision"] = {"n_independent_seeds": len(SEEDS), "avg_slope_SE": se_bar,
                              "avg_slope_CI_halfwidth": float(T49*se_bar),
                              "min_slope_distinguishable_from_zero_approx": float(T49*se_bar),
                              "per_sigma_SE_behavioural": persig_se}

out = f"{ROOT}/audit/v3/audit_results.json"
json.dump(report, open(out, "w"), indent=2)

# ---- console ----
print("STEP1  records=%d seeds=%d conds=%s sigmas=%s" % (s1["n_records"], s1["n_seeds"], s1["conditions"], s1["sigmas_present"]))
print("       static_cells=%d abrupt_cells=%d complete(static/abrupt)=%s/%s dup=%d" % (
    s1["static_cells"], s1["abrupt_cells"], s1["static_complete"], s1["abrupt_complete"], s1["duplicate_records"]))
print("       sigma_meas==decl=%s k_ok=%s prev0.5=%s sha_all=%s ver_all=%s sha_matches=%s wv_matched=%s" % (
    s1["measured_eq_declared_sigma"], s1["k_correct"], s1["prevalence_exact_0.5"], s1["prereg_sha_on_all"],
    s1["code_version_on_all"], s1["prereg_sha_matches_frozen"], s1["write_volume_matched"]))
print("STEP2  Delta re-derived from raw trajectory: max_abs_err_vs_stored=%.2e mismatched=%d" % (maxerr, mism))
print("STEP5  sigma slope  mean=%+.4f CI[%+.4f,%+.4f] SE=%.4f" % (
    report["step5_primary_CI_matrix"]["sigma_term_avg_slope"]["mean"],
    report["step5_primary_CI_matrix"]["sigma_term_avg_slope"]["ci_lo"],
    report["step5_primary_CI_matrix"]["sigma_term_avg_slope"]["ci_hi"],
    report["step5_primary_CI_matrix"]["sigma_term_avg_slope"]["se"]))
print("       chan-diff  mean=%+.4f CI[%+.4f,%+.4f]" % (
    report["step5_primary_CI_matrix"]["sigma_x_condition_diff"]["mean"],
    report["step5_primary_CI_matrix"]["sigma_x_condition_diff"]["ci_lo"],
    report["step5_primary_CI_matrix"]["sigma_x_condition_diff"]["ci_hi"]))
print("STEP6  R2_linear beh=%.4f arch=%.4f | quad_coef beh=%+.3f arch=%+.3f | max|resid_lin| beh=%.4f arch=%.4f" % (
    report["step6_shape"]["behavioural"]["R2_linear"], report["step6_shape"]["architectural"]["R2_linear"],
    report["step6_shape"]["behavioural"]["quad_coef"], report["step6_shape"]["architectural"]["quad_coef"],
    report["step6_shape"]["behavioural"]["max_abs_resid_linear"], report["step6_shape"]["architectural"]["max_abs_resid_linear"]))
print("STEP12 pooled_slope=%+.4f boot_slope_CI=[%+.4f,%+.4f] LOO=[%+.4f,%+.4f] chandiff_boot_CI=[%+.4f,%+.4f]" % (
    report["step12_robustness"]["pooled_ols_slope_ignoring_clusters"],
    *report["step12_robustness"]["bootstrap_avg_slope_ci95"],
    *report["step12_robustness"]["loo_avg_slope_min_max"],
    *report["step12_robustness"]["channel_diff_bootstrap_ci95"]))
print("STEP13 n_seeds=50 avg_slope_SE=%.4f CI_halfwidth=%.4f" % (se_bar, T49*se_bar))
print("wrote", out)
