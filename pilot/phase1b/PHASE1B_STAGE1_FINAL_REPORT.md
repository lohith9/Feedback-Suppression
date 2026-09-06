# PHASE1B — CORRECTED STAGE 1 FINAL REPORT
### 15 Aug 2026 · code `phase1b-corrected-3.0.0` · run `stage1_corrected_run_20260815_195408`
### Prereg SHA-256 `ca7ccb54def3…` (frozen, unmodified) · **Runtime ≈ 5 s** · **Cost $0.00**

---

## 1. Decision

# GO — with one significant negative finding that must be carried into the paper

The pre-registered hypothesis **survived**. Structured-state feedback measurably suppresses adaptation after a truth change, the effect is adaptation-specific (survives the mandatory static control), and it shows a systematic dose-response to Factor A. **However, RQ4 failed**: provenance-derived signals do *not* discriminate harmful from harmless configurations. That is reported as a result, not buried.

## 2. Setup

7 conditions × 2 truth regimes × 10 seeds = **140 runs**. 100 entities, 40 cycles, batch 40, base error 0.25, independent noise, abrupt shift at c15. Paired seeds (identical truth/noise realisations across all conditions).

## 3. Invariants — all PASS, verified before and during execution

| Invariant | Status | Evidence |
|---|---|---|
| Threshold | **PASS** | 0.70 / persist 3 read from frozen prereg; hash verified |
| Truth | **PASS** | transition exactly at c15; static regime constant |
| Seed | **PASS** | identical truth realisations across all conditions per seed |
| Write-volume | **PASS** | 4800 writes ON == 4800 OFF, every paired comparison |
| Configuration | **PASS** | config hash + code version stored on all 140 records |

## 4. Headline results

**Only the reference condition adapts.** wb=OFF/w=0.0 reaches ≥0.70 sustained in **10/10 seeds** (median 19.5 cycles). Every other condition is **censored 0/10**.

**Adaptation gap grows with time since the change** (paired, vs reference, abrupt shift):

| condition | +5 | +10 | +25 | same-direction |
|---|---|---|---|---|
| wb=OFF w=0.3 | 0.118 | 0.210 | **0.355** | 100 % |
| wb=OFF w=0.7 | 0.120 | 0.275 | **0.522** | 100 % |
| wb=OFF w=0.9 | 0.105 | 0.273 | **0.510** | 100 % |
| wb=ON w=0.0 | 0.103 | 0.265 | **0.507** | 100 % |

All +25 gaps have 95 % CIs excluding zero and paired *d* ≈ 6.7–7.9. At window 0 gaps are slightly negative (−0.03…−0.07) — immediately after the shift every condition is equally wrong; the divergence is in *recovery*, exactly as the hypothesis predicts.

**Mandatory static control — the effect is adaptation-specific:**

| condition | static gap @c40 | abrupt gap @c40 | difference |
|---|---|---|---|
| wb=OFF w=0.3 | 0.095 | 0.355 | **+0.260** |
| wb=OFF w=0.7 | 0.235 | 0.522 | **+0.287** |
| wb=OFF w=0.9 | 0.252 | 0.510 | **+0.258** |
| wb=ON w=0.0 | 0.255 | 0.507 | **+0.253** |

A static-truth arrested-improvement effect exists (0.10–0.26), but the abrupt-shift gap is roughly **twice** as large. The difference (~0.25–0.29) is the adaptation-specific component. This is the comparison the invalid run could not make.

## 5. Factor analysis

**Factor A (deference), write-back OFF, quality @c40:** 0.775 → 0.420 → 0.253 → 0.265 for w = 0.0/0.3/0.7/0.9. **Monotonic decline, saturating by w ≈ 0.7.** The dose-response the pre-registration asked for is present.

**Factor B (write-back), at matched deference:** ΔB = **−0.508** at w=0.0; **+0.015** at w=0.7; **+0.003** at w=0.9.

**Interaction: +0.510.** Strong and non-additive. Write-back alone (w=0.0) suppresses adaptation as completely as maximum deference does; once either channel is engaged the other adds nothing.

**Mechanism verified directly, not inferred:** with write-back ON, producer writes differ in **45.3 %** of cases between w=0.0 and w=0.9, yet **0 %** of decisions change. Write-back copies constitute 50 % of readable state and lock the majority so completely that fresh producer evidence cannot flip a single decision. This is genuine saturation, not an RNG artefact — explicitly tested.

## 6. Unexpected / negative findings

**RQ4 FAILED — provenance signals detect configuration, not harm.** AOD = 1.000 in *all seven* conditions. RR = 0.938 in every write-back-OFF condition, including **wb=OFF/w=0.0, the one condition that adapts perfectly (10/10)**, and 0.978 in every write-back-ON condition. The provenance metrics cannot separate the adapting system from the six failing ones. They indicate that a feedback *edge exists*, not that damage is occurring. The proposed early-warning/detector claim is **not supported** by this experiment and must be withdrawn or heavily qualified in the paper.

**Deference saturates earlier than expected** (~w=0.7 rather than rising to 1.0), so any real system with moderate-to-high deference is already at maximum suppression.

## 7. Comparison with the invalid prior run

| | Invalid run | Corrected run |
|---|---|---|
| Write volume | 4800 vs 3200 (**violated**) | 4800 == 4800 (**PASS**) |
| Deference weight | inert (identical traces) | **monotonic dose-response** |
| Threshold 0.85 | 100 % censored, uninformative | replaced by calibrated 0.70; reference adapts 10/10 |
| Static control | gap ≈ abrupt gap (uninterpretable) | abrupt gap ≈ 2× static gap (**adaptation-specific**) |
| Factors | conflated in one flag | orthogonal; interaction quantified (+0.510) |

The invalid run's exploratory 2×2 pattern is **independently reproduced** under the frozen pre-registered design — but it is the corrected run that carries evidential weight, per §25.

## 8. Threats to validity

Synthetic environment; binary task; deterministic non-LLM producers; independent-noise assumption (correlated noise implemented but **untested** — the largest remaining threat, since no-feedback recovery relies on independent evidence accumulation); abrupt total label flip is an extreme regime change; 10 seeds is exploratory, not robust (30 required for any claim); majority-vote aggregation is a strong simplification; deference and write-back rates in real systems are unmeasured.

## 9. Status

Stage 2 **not started**. No 30-seed confirmation, no correlated noise, no gradual drift, no LLM, no framework build — all awaiting explicit review per §9/§15.
