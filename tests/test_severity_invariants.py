"""Invariant tests for the shift-severity extension (I1-I9).
I10 (C1/C2 bit-exact regression) is checked separately via reproduce.py.

Runnable standalone (no pytest):  python3 tests/test_severity_invariants.py
Exits non-zero on any failure. Validates IMPLEMENTATION only — no science.
"""
import os, sys, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.scenarios.partial_shift import PartialShiftTruth
from src.experiments.severity_controller import run_severity_condition

N = 100
CHANGE = 15
GRID = [0.00, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00]
ENTS = [f"e{i:04d}" for i in range(N)]
FAILURES = []


def _truth(sigma, seed):
    return PartialShiftTruth({"sigma": sigma, "change_cycle": CHANGE},
                             random.Random(seed * 7919), ENTS)


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


# I1 — exact sigma (declared == measured; |S| == 2k)
print("I1 exact sigma")
for s in GRID:
    t = _truth(s, 1)
    k = round(s * (N // 2))
    check(f"  sigma={s}: measured==declared", abs(t.sigma_measured - s) < 1e-12,
          f"{t.sigma_measured} != {s}")
    check(f"  sigma={s}: |S|==2k=={2*k}", len(t.flip) == 2 * k, f"{len(t.flip)}")

# I2 — prevalence preserved exactly (50/50 pre and post) for every sigma
print("I2 prevalence preserved")
for s in GRID:
    t = _truth(s, 7)
    pre = t.prevalence(CHANGE - 1)
    post = t.prevalence(CHANGE)
    check(f"  sigma={s}: pre==0.5", abs(pre - 0.5) < 1e-12, f"{pre}")
    check(f"  sigma={s}: post==0.5", abs(post - 0.5) < 1e-12, f"{post}")

# I3 — nested flip subsets (sigma_low subset sigma_high), same seed
print("I3 nested subsets")
for seed in (1, 2, 3):
    sets = [(_truth(s, seed).flip_set(), s) for s in GRID]
    ok = all(sets[i][0] <= sets[i + 1][0] for i in range(len(sets) - 1))
    check(f"  seed={seed}: nested across grid", ok)

# I4 — sigma=0 == static (constant base, no change at any cycle)
print("I4 sigma=0 == static")
t0 = _truth(0.0, 4)
ok = all(t0.value(e, c) == t0.base[e] for e in ENTS for c in (1, CHANGE - 1, CHANGE, 40))
check("  sigma=0 truth constant == base", ok)
check("  sigma=0 flip set empty", len(t0.flip) == 0)

# I5 — sigma=1 flips all N
print("I5 sigma=1 full inversion")
t1 = _truth(1.0, 4)
check("  |S| == N", len(t1.flip) == N)
ok = all(t1.value(e, CHANGE) == 1 - t1.base[e] for e in ENTS)
check("  every entity inverted post-change", ok)

# I6 — seed pairing: feedback conditions share identical base truth at fixed (seed,sigma)
print("I6 seed pairing (shared truth across conditions)")
for s in (0.20, 0.60):
    truths = {}
    for cond in ("reference", "behavioural", "architectural"):
        _, tr = run_severity_condition(cond, s, "partial_shift", seed=9)
        truths[cond] = (dict(tr.base), tr.flip_set())
    base_ok = truths["reference"][0] == truths["behavioural"][0] == truths["architectural"][0]
    flip_ok = truths["reference"][1] == truths["behavioural"][1] == truths["architectural"][1]
    check(f"  sigma={s}: identical base across conditions", base_ok)
    check(f"  sigma={s}: identical flip set across conditions", flip_ok)

# I7 — RNG isolation: pre-change rows bit-identical across sigma (fixed seed, condition)
print("I7 RNG isolation (pre-change bit-identical across sigma)")
for cond in ("reference", "behavioural", "architectural"):
    rows_a, _ = run_severity_condition(cond, 0.20, "partial_shift", seed=5)
    rows_b, _ = run_severity_condition(cond, 0.80, "partial_shift", seed=5)
    pre_a = rows_a[:CHANGE - 1]   # cycles 1..14
    pre_b = rows_b[:CHANGE - 1]
    check(f"  {cond}: cycles 1..{CHANGE-1} identical across sigma", pre_a == pre_b)

# I8 — write volume: readable (wb=True) vs inert (wb=False) identical write counts (w=0)
print("I8 write-volume invariant (Factor B)")
for s in (0.0, 0.20, 1.00):
    ref, _ = run_severity_condition("reference", s, "partial_shift", seed=3)      # wb False, w0
    arch, _ = run_severity_condition("architectural", s, "partial_shift", seed=3)  # wb True, w0
    check(f"  sigma={s}: writes(ref)==writes(arch)", ref[-1]["writes"] == arch[-1]["writes"],
          f"{ref[-1]['writes']} != {arch[-1]['writes']}")

# I9 — non-interference: instrument ON vs OFF -> identical system quantities
print("I9 non-interference (instrument on/off)")
for cond in ("reference", "architectural"):
    on, _ = run_severity_condition(cond, 0.40, "partial_shift", seed=6, instrument=True)
    off, _ = run_severity_condition(cond, 0.40, "partial_shift", seed=6, instrument=False)
    same = all(on[i]["quality"] == off[i]["quality"] and on[i]["writes"] == off[i]["writes"]
               and on[i]["observations"] == off[i]["observations"]
               and on[i]["cum_regret"] == off[i]["cum_regret"] for i in range(len(on)))
    check(f"  {cond}: quality/writes/obs/regret identical on vs off", same)

print()
if FAILURES:
    print(f"SEVERITY INVARIANTS: {len(FAILURES)} FAILURE(S): {FAILURES}")
    sys.exit(1)
print("ALL SEVERITY INVARIANTS PASSED (I1-I9)")
