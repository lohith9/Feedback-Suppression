# V4 aggregation-rule ablation: results summary

Pre-registration: `preregistration/AGGREGATION_ABLATION_V4.yaml` (SHA-256 6332c73b...2d4e), committed and pushed in b12c3ff **before** any V4 data were generated. Designed after the ACDSA 2027 reviews of Paper 872.

Raw: `results/raw/aggregation_v4_20261121_183749/aggregation_v4.json` (1200 runs, seeds 101-130). Locked analysis: `analyze_aggregation_v4.py` -> `results/raw/aggregation_v4_20261121_183749/analysis_v4.json`.

Invariants: I1 CUM reproduces published C1 raw 240/240 bit-exactly; I2 write volume equal across write-back settings; I3 paired design. All PASS. No deviations from the pre-registration.

| Rule | Deference | Write-back | Both | Interaction (95% CI) |
|---|---|---|---|---|
| CUM | 0.283 PRESENT | 0.283 PRESENT | 0.283 PRESENT | not identifiable (saturated) |
| WIN10 | 0.178 PRESENT | 0.143 PRESENT | 0.411 PRESENT | +0.089 [+0.055,+0.124] SUPER-ADDITIVE |
| EXP | 0.167 PRESENT | 0.037 ABSENT | 0.398 PRESENT | +0.194 [+0.159,+0.229] SUPER-ADDITIVE |
| WIN5 | 0.013 ABSENT | -0.019 ABSENT | 0.014 ABSENT | not identifiable (no channel effect) |
| LWW | 0.009 ABSENT | 0.000 ABSENT | 0.009 ABSENT | not identifiable (no channel effect) |

Values are Delta_adapt (abrupt-minus-static feedback gap at cycle 40, within seed). Under LWW, write-back alone is run-for-run identical to the reference: the decision always reads the producer's same-cycle write.

Interpretation (simulator only): the adaptation penalty requires a read path that retains long pre-shift history; with short memory it is absent. Where neither channel saturates, the channels compound super-additively. Short-memory rules cost static accuracy (reference q40 static: CUM 0.983, WIN5 0.811, LWW 0.739).
