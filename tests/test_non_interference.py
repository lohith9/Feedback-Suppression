"""NON-INTERFERENCE GATE (frozen ARCHITECTURE_DESIGN.md §4, Invariant I-1).
Run each reference condition with instrumentation ON vs OFF; the system under
test (decisions, writes, ground-truth scoring, regret) MUST be identical.
This would FAIL if provenance instrumentation consumed system RNG or mutated
state. It is a genuine test, not a tautology."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.experiments.controller import run_c1_condition, C1_CONDITIONS, C1_REGIMES

def test_instrumentation_is_read_only():
    checked = 0
    for tm in C1_REGIMES:
        for wb, w in C1_CONDITIONS:
            for seed in range(1, 6):
                on = run_c1_condition(tm, w, wb, seed, instrument=True)
                off = run_c1_condition(tm, w, wb, seed, instrument=False)
                for a, b in zip(on, off):
                    # System-under-test quantities must match exactly.
                    assert a["cycle"] == b["cycle"]
                    assert a["quality"] == b["quality"], f"DECISION CHANGED {tm} wb={wb} w={w} s={seed} c{a['cycle']}"
                    assert a["writes"] == b["writes"], "WRITE COUNT CHANGED"
                    assert a["observations"] == b["observations"], "RNG/OBS ORDER CHANGED"
                    assert a["cum_regret"] == b["cum_regret"], "SCORING CHANGED"
                    # Instrumentation-only channel is allowed to differ (off => 0).
                checked += 1
    assert checked == 2 * 7 * 5
    print(f"non-interference OK: {checked} conditions; decisions/writes/regret identical ON vs OFF")

if __name__ == "__main__":
    test_instrumentation_is_read_only()
    print("NON-INTERFERENCE TEST PASSED")
