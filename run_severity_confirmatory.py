#!/usr/bin/env python3
"""V3 CONFIRMATORY runner — 50 seeds / 1050 runs, executed EXACTLY as frozen.
Frozen prereg: preregistration/SHIFT_SEVERITY_V3.yaml (SHA 2301d948…504b).
Aborts on any invariant failure. Writes immutable raw with full provenance.
Does NOT analyze or interpret; that is a separate, locked step.
"""
import os, sys, json, time, hashlib, datetime
ROOT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ROOT)
from src.experiments.severity_controller import (
    run_severity_condition, SEVERITY_CONDITIONS, CODE_VERSION)

PREREG = "preregistration/SHIFT_SEVERITY_V3.yaml"
PREREG_SHA = "2301d9485133669e411e203d3a66e0719933d97b824c0d4d3ad55957f3a8504b"
SEEDS = list(range(1, 51))
SIGMAS_NONZERO = [0.10, 0.20, 0.40, 0.60, 0.80, 1.00]
CONDITIONS = ["reference", "behavioural", "architectural"]
CHANGE, CYCLES, N = 15, 40, 100

def _abort(msg):
    print(f"ABORT: {msg}"); sys.exit(2)

# ---- gate: freeze + baseline -------------------------------------------------
if hashlib.sha256(open(PREREG, "rb").read()).hexdigest() != PREREG_SHA:
    _abort("prereg SHA mismatch")

def qtraj(rows): return [r["quality"] for r in rows]
def q40(rows): return rows[-1]["quality"]
def adaptation(rows, thr=0.70, sustain=3, change=CHANGE):
    run = 0
    for r in rows:
        if r["cycle"] <= change:
            continue
        if r["quality"] >= thr:
            run += 1
            if run >= sustain:
                return (r["cycle"] - change - sustain + 1), True   # cycles-after-change to start of window
        else:
            run = 0
    return None, False

t0 = time.time()
TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUT = f"results/raw/severity_run_{TS}"
os.makedirs(OUT, exist_ok=True)

# ---- run everything; collect raw ---------------------------------------------
# static once per (seed, condition); abrupt per (seed, condition, sigma)
static = {}   # (seed,cond) -> dict
abrupt = {}   # (seed,cond,sigma) -> dict
flip_by_seed_sigma = {}  # (seed,sigma) -> frozenset  (for I3 nesting + I6)
runs = 0

def record(rows, truth, seed, cond, sigma, regime):
    global runs; runs += 1
    at, adapted = adaptation(rows)
    return {
        "seed": seed, "condition": cond, "sigma": sigma,
        "k": round(sigma * (N // 2)), "truth_regime": regime,
        "sigma_measured": truth.sigma_measured,
        "pre_shift_prevalence": truth.prevalence(CHANGE - 1),
        "post_shift_prevalence": truth.prevalence(CHANGE),
        "q_final": q40(rows), "quality_trajectory": qtraj(rows),
        "adaptation_time": at, "adapted": adapted,
        "writes": rows[-1]["writes"], "observations": rows[-1]["observations"],
        "AOD": rows[-1]["AOD"], "RR": rows[-1]["RR"],
        "code_version": CODE_VERSION, "prereg_sha256": PREREG_SHA, "timestamp": TS,
    }

for seed in SEEDS:
    for cond in CONDITIONS:
        rows, tr = run_severity_condition(cond, 0.0, "static", seed=seed)
        # I1/I2 (static == sigma0)
        if len(tr.flip) != 0: _abort(f"I4 static flip nonempty seed{seed}")
        if abs(tr.prevalence(CHANGE) - 0.5) > 1e-12: _abort(f"I2 prevalence static seed{seed}")
        static[(seed, cond)] = record(rows, tr, seed, cond, 0.0, "static")
    for s in SIGMAS_NONZERO:
        seed_flip = None
        for cond in CONDITIONS:
            rows, tr = run_severity_condition(cond, s, "partial_shift", seed=seed)
            # per-run invariants
            if abs(tr.sigma_measured - s) > 1e-12: _abort(f"I1 sigma seed{seed} s{s}")
            if abs(tr.prevalence(CHANGE - 1) - 0.5) > 1e-12 or abs(tr.prevalence(CHANGE) - 0.5) > 1e-12:
                _abort(f"I2 prevalence seed{seed} s{s}")
            fs = frozenset(tr.flip_set())
            if seed_flip is None:
                seed_flip = fs
            elif fs != seed_flip:               # I6: same truth across conditions
                _abort(f"I6 flip differs across conditions seed{seed} s{s}")
            abrupt[(seed, cond, s)] = record(rows, tr, seed, cond, s, "partial_shift")
        flip_by_seed_sigma[(seed, s)] = seed_flip

# I3 nesting across sigma per seed
for seed in SEEDS:
    prev = frozenset()
    for s in SIGMAS_NONZERO:
        cur = flip_by_seed_sigma[(seed, s)]
        if not prev <= cur: _abort(f"I3 not nested seed{seed} at s{s}")
        prev = cur
    if len(flip_by_seed_sigma[(seed, 1.00)]) != N: _abort(f"I5 sigma1 not full seed{seed}")

# ---- enrich with feedback_gap / Delta_adapt (derived) ------------------------
records = []
for seed in SEEDS:
    qrs = static[(seed, "reference")]["q_final"]
    for cond in CONDITIONS:
        # static record
        rec = dict(static[(seed, cond)])
        rec["feedback_gap_static"] = (qrs - rec["q_final"]) if cond != "reference" else 0.0
        rec["feedback_gap_abrupt"] = None; rec["delta_adapt"] = None; rec["q_ref_abrupt"] = None
        rec["config_hash"] = hashlib.sha256(json.dumps(
            {"cond":cond,"sigma":0.0,"regime":"static","N":N,"change":CHANGE,"cycles":CYCLES},
            sort_keys=True).encode()).hexdigest()[:12]
        records.append(rec)
    for s in SIGMAS_NONZERO:
        qra = abrupt[(seed, "reference", s)]["q_final"]
        gs_ref = 0.0
        for cond in CONDITIONS:
            rec = dict(abrupt[(seed, cond, s)])
            gs = (qrs - static[(seed, cond)]["q_final"]) if cond != "reference" else 0.0
            ga = (qra - rec["q_final"]) if cond != "reference" else 0.0
            rec["feedback_gap_static"] = gs
            rec["feedback_gap_abrupt"] = ga
            rec["delta_adapt"] = (ga - gs) if cond != "reference" else 0.0
            rec["q_ref_abrupt"] = qra
            rec["config_hash"] = hashlib.sha256(json.dumps(
                {"cond":cond,"sigma":s,"regime":"partial_shift","N":N,"change":CHANGE,"cycles":CYCLES},
                sort_keys=True).encode()).hexdigest()[:12]
            records.append(rec)

json.dump(records, open(f"{OUT}/severity.json", "w"))
meta = {"prereg_sha256": PREREG_SHA, "code_version": CODE_VERSION, "timestamp": TS,
        "seeds": SEEDS, "sigmas_nonzero": SIGMAS_NONZERO, "conditions": CONDITIONS,
        "runs": runs, "n_records": len(records),
        "invariants_checked": ["I1","I2","I3","I4","I5","I6"],
        "note": "I7/I8/I9 covered by tests/test_severity_invariants.py; I10 by reproduce.py"}
json.dump(meta, open(f"{OUT}/manifest.json", "w"), indent=2)

print(f"runs={runs} (expected 1050)  records={len(records)}")
print(f"raw -> {OUT}/severity.json")
print(f"invariants I1-I6 per-run: PASS")
print(f"runtime={time.time()-t0:.1f}s  cost=$0.00")
print(OUT)
