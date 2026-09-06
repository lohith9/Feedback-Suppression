# REPRODUCIBILITY.md
### Feedback Suppression of Adaptation in AI-Written Structured State — full reproduction instructions
### Total research cost to reproduce everything: **$0.00**

---

## 1. What this reproduces

Every number in the manuscript: the C1 confirmatory experiment (420 runs), the C2 correlated-noise robustness experiment (360 runs), all analyses, and all figures.

## 2. Environment

- Python 3.10+ (developed on 3.10.12)
- `matplotlib` (figures only). No other third-party dependency.
- CPU only. No GPU, no network access, no API key, no account.
- Runtime: C1 ≈ 5 s, C2 ≈ 18 s, figures ≈ 20 s. Whole suite under a minute on a laptop.

**Zero-cost statement.** No component of this research requires a paid API, hosted model, cloud instance, paid dataset, or commercial tool. The simulator contains no language model. Anyone can re-run the complete study on a personal machine at no cost — this was a hard project constraint, not an afterthought.

## 3. Commands

```bash
# --- C1: confirmatory experiment (7 conditions x 2 regimes x 30 seeds) ---
cd pilot/phase1b
N_SEEDS=30 python3 run_stage1_corrected.py
#   -> results/raw/stage1_corrected_run_<TIMESTAMP>_n30/
python3 analyze_stage1_corrected.py results/raw/stage1_corrected_run_<TIMESTAMP>_n30
python3 plot_stage1_corrected.py    results/raw/stage1_corrected_run_<TIMESTAMP>_n30

# --- C2: correlated-noise robustness (3 conditions x 4 rho x 30 seeds) ---
python3 sim_c2.py
#   -> results/raw/c2_correlated_run_<TIMESTAMP>/
python3 analyze_c2.py results/raw/c2_correlated_run_<TIMESTAMP>
python3 plot_c2.py    results/raw/c2_correlated_run_<TIMESTAMP>
```

Every runner verifies its invariants **before** producing results and aborts on violation.

## 4. Experiment IDs (as published)

| Experiment | Run directory | Records |
|---|---|---|
| C1 confirmatory, 30 seeds | `stage1_corrected_run_20260816_002729_n30` | 420 |
| C1 initial, 10 seeds (exploratory) | `stage1_corrected_run_20260815_195408` | 140 |
| C2 correlated noise, 30 seeds | `c2_correlated_run_20260816_125534` | 360 |
| Phase 0 pilot | `pilot/results/raw/` | 30 |
| **Invalid Stage 1 (historical)** | `stage1_INVALID_v1.json` + `archive/invalid_runs/` | preserved unmodified |

The invalid run is deliberately retained. It documents a real methodological failure (write-volume mismatch, inert weight parameter, unreachable threshold) and the corrections that followed.

## 5. Configuration

- **C1 pre-registration (frozen):** `pilot/phase1b/preregistration/STAGE1_CORRECTED.yaml`, SHA-256 `ca7ccb54def38253bd603b344c7c2c81832fe4b439263f2633209e106c1e0400`
- **C2 pre-registration (frozen):** `pilot/phase1b/preregistration/C2_CORRELATED_NOISE.yaml`
- Adaptation threshold: quality ≥ 0.70 sustained 3 cycles (calibrated from a **control-only** run before treatment conditions were observed)
- Seeds: 1–30, paired across all conditions
- Simulator: 100 entities, 40 cycles, batch 40, error rate 0.25, truth shift at cycle 15

Each result record stores its config hash, code version, seed, and run timestamp.

## 6. Expected outputs

| Quantity | Expected |
|---|---|
| Factor A quality @c40 (w = 0.0/0.3/0.7/0.9) | 0.764 / 0.396 / 0.237 / 0.237 |
| Adaptation gap range @+25 | 0.368 – 0.527 |
| Reference adaptation rate | 20/30 |
| Feedback-condition adaptation rate | 0/30 (all) |
| Factor B ΔB at w=0.0 | −0.527 |
| Interaction A×B | +0.527 |
| C2 retention at ρ=0.9 | 94% behavioural, 92% architectural |
| C2 ρ=0 vs C1 regression | agreement within 0.01 |
| AOD (all conditions) | 1.000 |
| RR | 0.938 (inert write-back) / 0.978 (readable) |

Runs are deterministic and seeded: these values reproduce exactly, not approximately.

## 7. Verifying the paper's numbers

`paper/notes/` contains the QA scripts used for the numerical-consistency audit, which re-derives every headline figure directly from raw results. All 8 checks passed at submission time.

## 8. Raw-data policy

Raw results are immutable. Analyses read from `results/raw/` and write only to `results/processed/`, `results/analysis/`, and `results/figures/`. No run was excluded; censored adaptation times are reported as censored rather than dropped.
