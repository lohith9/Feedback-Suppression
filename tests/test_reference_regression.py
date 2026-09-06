"""REGRESSION GATE — new architecture must reproduce the 780 published runs
bit-exactly. Compares src.experiments.controller output against the immutable
raw JSON. Any difference => STOP (migration changed behaviour)."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.experiments.controller import run_c1_condition, run_c2_condition, C1_CONDITIONS, C1_REGIMES

C1_RAW = os.path.join(ROOT, "pilot/phase1b/results/raw/stage1_corrected_run_20260816_002729_n30/stage1_corrected.json")
C2_RAW = os.path.join(ROOT, "pilot/phase1b/results/raw/c2_correlated_run_20260816_125534/c2_correlated.json")
KEYS = ["cycle", "quality", "AOD", "RR", "writes", "observations", "cum_regret"]

def _rows_equal(a, b):
    if len(a) != len(b): return False
    for x, y in zip(a, b):
        for k in KEYS:
            if x[k] != y[k]:                      # exact equality, no tolerance
                return False
    return True

def test_c1_regression():
    raw = json.load(open(C1_RAW))
    idx = {(r["truth_mode"], r["writeback"], r["deference_weight"], r["seed"]): r for r in raw}
    checked = 0
    for tm in C1_REGIMES:
        for wb, w in C1_CONDITIONS:
            for seed in range(1, 6):             # seeds 1-5 per directive
                new = run_c1_condition(tm, w, wb, seed)
                pub = idx[(tm, wb, w, seed)]["rows"]
                assert _rows_equal(new, pub), f"C1 MISMATCH {tm} wb={wb} w={w} s={seed}"
                checked += 1
    assert checked == 2 * 7 * 5
    print(f"C1 regression OK: {checked} conditions bit-exact")

def test_c2_regression():
    raw = json.load(open(C2_RAW))
    idx = {(r["rho"], r["condition"], r["seed"]): r for r in raw}
    conds = {"reference": (False, 0.0), "behavioural": (False, 0.7), "architectural": (True, 0.0)}
    checked = 0
    for rho in [0.0, 0.3, 0.6, 0.9]:
        for name, (wb, w) in conds.items():
            for seed in range(1, 6):
                new = run_c2_condition(name, w, wb, rho, seed)
                pub = idx[(rho, name, seed)]["rows"]
                assert _rows_equal(new, pub), f"C2 MISMATCH {name} rho={rho} s={seed}"
                checked += 1
    assert checked == 4 * 3 * 5
    print(f"C2 regression OK: {checked} conditions bit-exact")

if __name__ == "__main__":
    test_c1_regression(); test_c2_regression()
    print("ALL REGRESSION TESTS PASSED")
