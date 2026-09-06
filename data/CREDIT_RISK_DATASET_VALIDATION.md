> **FINAL: credit-risk ABANDONED as adaptation test (boundary finding). Dataset verification stands; see CREDIT_RISK_BOUNDARY_FINDING.md.**

# CREDIT_RISK_DATASET_VALIDATION.md
### 18 Aug 2026 · **REAL UCI DATA LOADED AND VERIFIED**

## File provided
`data/raw/credit_default.xls` — native UCI 350 Excel (OLE2 Composite Document, 5.54 MB).
Deterministically converted to `data/raw/credit_default.csv` (header = feature-name row; `ID` column dropped; target name kept verbatim). Conversion reads the file you placed — not a download.

## Hashes
| file | SHA-256 |
|---|---|
| `credit_default.xls` (provided) | `30c6be3abd8dcfd3e6096c828bad8c2f011238620f5369220bd60cfc82700933` |
| `credit_default.csv` (derived) | `eeaaa5addd59a2c56e82cbfca996f37ad98714c0237f1a3cbc8d7e973102966d` |

## Schema (verified)
- Rows: **30,000** · Feature columns: **23** (+ target) · Missing cells: **0**
- Target: `default payment next month` ∈ {0,1}
- **Native prevalence: 0.2212** (= 6636/30000, matches the documented UCI figure)
- Columns: `LIMIT_BAL, SEX, EDUCATION, MARRIAGE, AGE, PAY_0, PAY_2..PAY_6, BILL_AMT1..6, PAY_AMT1..6, default payment next month`
- Identity: UCI ID 350, Default of Credit Card Clients, DOI 10.24432/C55S3H, Yeh (2009), CC BY 4.0.

## SOURCE FACTS vs OUR TRANSFORMATIONS
| SOURCE FACTS (UCI 350) | OUR SIMULATED TRANSFORMATIONS |
|---|---|
| 30,000 clients, 23 features, 0 missing | deterministic stratified 100-client sample (prevalence preserved) |
| native target ∈ {0,1}, prevalence 0.2212 | **baseline_truth = native target, verbatim** |
| 6 native monthly periods | 40 **simulated** decision cycles (Option B) |
| observed feature→default relationships | calibration model on a **disjoint** subset → counterfactual post-shift only |

## Status
Dataset verification **PASSED**. The 5-seed real pilot ran; decision is **MODIFY** (shift too weak — see `CREDIT_RISK_REAL_PILOT_REPORT.md`). Baseline C1/C2 untouched and bit-exact.
