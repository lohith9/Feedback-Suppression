# data/ — dataset provenance and instructions

## UCI Default of Credit Card Clients (UCI ID 350)
Used **only** by the external-grounding boundary experiment (UCI). Third-party
data — **not** created or re-licensed by this repository.

- **Source:** https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients
- **DOI:** 10.24432/C55S3H
- **License:** CC BY 4.0
- **Required citation:** I-C. Yeh and C-H. Lien, "The comparisons of data mining
  techniques for the predictive accuracy of probability of default of credit card
  clients," *Expert Systems with Applications*, 36(2):2473–2480, 2009.

## Files and checksums
The raw files are **git-ignored** (see repo `.gitignore`); download from UCI and
place under `data/raw/`. Verify integrity against:

| File | SHA-256 |
|---|---|
| `credit_default.xls` (native UCI Excel) | `30c6be3abd8dcfd3e6096c828bad8c2f011238620f5369220bd60cfc82700933` |
| `credit_default.csv` (derived: header = feature-name row; `ID` dropped; target kept verbatim) | `eeaaa5addd59a2c56e82cbfca996f37ad98714c0237f1a3cbc8d7e973102966d` |

Schema: 30,000 rows × 23 feature columns + target `default payment next month` ∈ {0,1}; native prevalence 0.2212; 0 missing cells.

## Important scientific note
The UCI data is an **empirical substrate only**. The feedback loop studied in this
project is **introduced by our simulator** — the dataset itself contains no AI
feedback loop. The native default label is used **verbatim as baseline truth**; a
calibrated counterfactual (fit on a disjoint subset) introduces a realistic
partial regime shift for the boundary analysis. See `CREDIT_RISK_BOUNDARY_FINDING.md`
and `data/CREDIT_RISK_DATASET_VALIDATION.md`.
