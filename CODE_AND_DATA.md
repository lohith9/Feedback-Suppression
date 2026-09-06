# Code and Data — where everything lives

**Yes, there is code, and every number in the paper came from running it.**
Nothing in the manuscript was estimated, assumed, or hand-computed.

## The code that produced the results

| File | Role |
|---|---|
| `pilot/sim.py` | Provenance layer: assertion store, why-provenance ancestry, AOD/RR |
| `pilot/phase1b/sim1c.py` | **C1 simulator** — Factor A (deference) x Factor B (write-back) |
| `pilot/phase1b/sim_c2.py` | **C2 simulator** — adds correlated (persistent-entity-bias) noise |
| `pilot/phase1b/truth_process.py` | Truth regimes: static, abrupt shift, drift |
| `pilot/phase1b/noise_process.py` | Observation-noise models |
| `pilot/phase1b/feedback_policy.py` | Producer deference policy |
| `pilot/phase1b/run_stage1_corrected.py` | C1 runner; enforces all 5 invariants, aborts on violation |
| `pilot/phase1b/analyze_stage1_corrected.py` | C1 analysis (Tables 1-6) |
| `pilot/phase1b/analyze_c2.py` | C2 analysis |
| `pilot/phase1b/plot_stage1_corrected.py`, `plot_c2.py` | Figure generation |

## Pre-registrations (frozen before the confirmatory runs)

- `pilot/phase1b/preregistration/STAGE1_CORRECTED.yaml` — SHA-256 `ca7ccb54def3…`
- `pilot/phase1b/preregistration/C2_CORRELATED_NOISE.yaml`

## Raw results (44 JSON files, never overwritten)

- C1 confirmatory, 30 seeds, 420 runs: `pilot/phase1b/results/raw/stage1_corrected_run_20260816_002729_n30/`
- C2 robustness, 30 seeds, 360 runs: `pilot/phase1b/results/raw/c2_correlated_run_20260816_125534/`
- Phase 0 pilot: `pilot/results/raw/`
- Invalid historical run (preserved deliberately): `pilot/phase1b/results/raw/stage1_INVALID_v1.json` and `pilot/archive/invalid_runs/`

## Reproduce everything (~30 seconds, $0.00)

```bash
cd pilot/phase1b
N_SEEDS=30 python3 run_stage1_corrected.py          # C1: 420 runs
python3 analyze_stage1_corrected.py results/raw/stage1_corrected_run_<TS>_n30
python3 sim_c2.py                                    # C2: 360 runs
python3 analyze_c2.py results/raw/c2_correlated_run_<TS>
```

Python 3.10+, `matplotlib` for figures only. No API key, no model download, no network, no GPU.
Runs are deterministic and seeded: the published values reproduce **exactly**, not approximately.
Expected values are listed in `REPRODUCIBILITY.md` §6 for verification.

## Note on one deletion

`sim1b.py` (the code for the *invalid* earlier Stage 1) was removed during cleanup as
superseded. Its raw outputs are still preserved in `pilot/archive/invalid_runs/` and
`stage1_INVALID_v1.json`, and the defects it exhibited are documented in
`pilot/phase1b/PHASE1B_FINDINGS.md`. The valid C1/C2 results do not depend on it.
