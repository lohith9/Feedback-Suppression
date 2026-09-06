#!/usr/bin/env python3
"""SMOKE TEST ONLY for the shift-severity extension (V3).

Scope: validate the implementation end-to-end on a TINY grid. This is NOT the
confirmatory run and does NOT interpret any severity curve.
  seeds = 3 ; sigma subset = {0.00 (static), 0.20, 0.60, 1.00} ; 3 conditions.
  runs  = static 3x3=9 + abrupt 3x3x3=27 = 36.

The 50-seed / 1050-run confirmatory experiment is NOT performed here and is not
authorized until this smoke passes AND a human approves.
"""
import os, sys, time
ROOT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ROOT)
from src.experiments.severity_controller import run_severity_condition, CODE_VERSION

SEEDS = [1, 2, 3]
SIGMAS_ABRUPT = [0.20, 0.60, 1.00]     # sigma=0 represented by the static runs
CONDITIONS = ["reference", "behavioural", "architectural"]
FEEDBACK = ["behavioural", "architectural"]
CHANGE = 15

def qfinal(rows):           # quality at +25 cycles after change (cycle 40)
    return rows[-1]["quality"]

t0 = time.time()
runs = 0

# --- static once per (seed, condition), reused across sigma (M3) --------------
q_static = {}     # (seed, cond) -> q@40
for seed in SEEDS:
    for cond in CONDITIONS:
        rows, tr = run_severity_condition(cond, 0.0, "static", seed=seed); runs += 1
        q_static[(seed, cond)] = qfinal(rows)
        assert abs(tr.sigma_measured - 0.0) < 1e-12 and len(tr.flip) == 0

# --- abrupt partial_shift ------------------------------------------------------
q_abrupt = {}     # (seed, cond, sigma) -> q@40
sigma_ok = True
for seed in SEEDS:
    for s in SIGMAS_ABRUPT:
        for cond in CONDITIONS:
            rows, tr = run_severity_condition(cond, s, "partial_shift", seed=seed); runs += 1
            q_abrupt[(seed, cond, s)] = qfinal(rows)
            if abs(tr.sigma_measured - s) > 1e-12 or abs(tr.prevalence(CHANGE) - 0.5) > 1e-12:
                sigma_ok = False

# --- assemble Delta_adapt (pipeline demonstration only; NOT interpreted) -------
def mean(xs): return sum(xs) / len(xs)

print(f"code_version={CODE_VERSION}  runs={runs}  seeds={SEEDS}  sigma_abrupt={SIGMAS_ABRUPT}")
print(f"sigma/prevalence exact on all runs: {sigma_ok}")
print("\nPIPELINE OUTPUT (means over 3 seeds — NOT a scientific result, smoke only):")
print(f"{'cond':13} {'sigma':>5} {'gap_static':>11} {'gap_abrupt':>11} {'Delta_adapt':>12}")
for cond in FEEDBACK:
    gs = mean([q_static[(seed, 'reference')] - q_static[(seed, cond)] for seed in SEEDS])
    for s in SIGMAS_ABRUPT:
        ga = mean([q_abrupt[(seed, 'reference', s)] - q_abrupt[(seed, cond, s)] for seed in SEEDS])
        print(f"{cond:13} {s:5.2f} {gs:11.3f} {ga:11.3f} {ga - gs:12.3f}")

print(f"\nreference q@40 (static / abrupt by sigma), means:")
rs = mean([q_static[(seed, 'reference')] for seed in SEEDS])
print(f"  static: {rs:.3f}  | " + "  ".join(f"s={s}:{mean([q_abrupt[(seed,'reference',s)] for seed in SEEDS]):.3f}" for s in SIGMAS_ABRUPT))

print(f"\nruntime={time.time()-t0:.2f}s  cost=$0.00")
print("SMOKE PIPELINE OK (implementation exercised; NO confirmatory run performed)")
