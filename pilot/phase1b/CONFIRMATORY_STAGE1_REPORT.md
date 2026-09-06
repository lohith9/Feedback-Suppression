# CONFIRMATORY_STAGE1_REPORT.md — Stage C1 (30 seeds)
### 16 Aug 2026 · run `stage1_corrected_run_20260816_002729_n30` · code `phase1b-corrected-3.0.0`
### Prereg SHA-256 `ca7ccb54def3…` (frozen, unmodified) · 420 runs · **Cost $0.00**

---

## 1. Protocol

Frozen Stage 1 design executed unchanged: 7 conditions × 2 truth regimes × **30 seeds** = 420 runs. 100 entities, 40 cycles, batch 40, base error rate 0.25, independent noise, abrupt shift at cycle 15, paired seeds, adaptation threshold 0.70 sustained 3 cycles.

All five invariants verified before and during execution: **threshold PASS** (read from frozen prereg, hash checked), **truth PASS** (transition exactly at c15; static regime constant), **seed PASS** (identical truth/noise realisations across conditions), **write-volume PASS** (4800 == 4800 on every paired comparison), **configuration PASS** (config hash + code version stored on all 420 records).

## 2. Deviations from protocol

**One, non-scientific:** the seed count was parameterised via an environment variable (`N_SEEDS`) so the same runner produces the n=10 and n=30 runs. No hypothesis, threshold, condition, metric, or stopping rule was altered. A cosmetic display bug in the analysis script (adapted count hard-coded as `/10`) was corrected to `/{len(SEEDS)}`; it affected the printed denominator only, never a computed value.

**No seeds were excluded. No censored runs were dropped.**

## 3. Results (30 seeds)

### Adaptation

| condition | adapted | median cycles |
|---|---|---|
| **wb=OFF w=0.0 (reference)** | **20/30** | 20.0 |
| wb=OFF w=0.3 | 0/30 | censored |
| wb=OFF w=0.7 | 0/30 | censored |
| wb=OFF w=0.9 | 0/30 | censored |
| wb=ON w=0.0 | 0/30 | censored |
| wb=ON w=0.7 | 0/30 | censored |
| wb=ON w=0.9 | 0/30 | censored |

Only the no-feedback reference ever recovers to the pre-registered threshold. **Note the correction against n=10:** at 10 seeds the reference adapted 10/10; at 30 seeds it adapts **20/30 (67 %)**. The smaller run was optimistic. The qualitative contrast (only the reference adapts; every feedback condition is 0/30) is unchanged and is in fact sharper.

### Adaptation gap (paired, vs reference, abrupt shift)

| condition | +5 | +10 | **+25** | 95 % CI (+25) | *d* | same-direction |
|---|---|---|---|---|---|---|
| wb=OFF w=0.3 | 0.094 | 0.181 | **0.368** | [0.342, 0.395] | 5.02 | 100 % |
| wb=OFF w=0.7 | 0.083 | 0.235 | **0.527** | [0.491, 0.562] | 5.34 | 100 % |
| wb=OFF w=0.9 | 0.069 | 0.233 | **0.527** | [0.491, 0.564] | 5.16 | 100 % |
| wb=ON w=0.0 | 0.069 | 0.232 | **0.527** | [0.490, 0.563] | 5.16 | 100 % |
| wb=ON w=0.7 | 0.069 | 0.232 | **0.527** | [0.490, 0.563] | 5.16 | 100 % |
| wb=ON w=0.9 | 0.069 | 0.232 | **0.527** | [0.490, 0.563] | 5.16 | 100 % |

All +25 gaps: CIs exclude zero, paired *d* ≈ 5.0–5.3, **100 % of seeds in the same direction**. At window 0 gaps are slightly negative (−0.03…−0.07): immediately after the shift every condition is equally wrong. The divergence is entirely in **recovery**, which is what the hypothesis predicts.

### Static control (mandatory comparator)

| condition | static gap @c40 | abrupt gap @c40 | **difference** |
|---|---|---|---|
| wb=OFF w=0.3 | 0.077 | 0.368 | **+0.291** |
| wb=OFF w=0.7 | 0.212 | 0.527 | **+0.315** |
| wb=OFF w=0.9 | 0.222 | 0.527 | **+0.305** |
| wb=ON w=0.0 | 0.223 | 0.527 | **+0.303** |

A static arrested-improvement effect exists (0.08–0.22), but the abrupt-shift gap is roughly **2.4× larger**. The ~0.30 difference is the adaptation-specific component. **RQ1: supported.**

## 4. Statistical analysis

Paired design (identical stochastic realisations per seed across conditions), so all comparisons are within-seed differences. Reported: mean, sd, 95 % CI, paired Cohen's *d*, per-seed direction. Effect sizes at +25 are large (*d* ≈ 5) with unanimous per-seed direction — but note these are **simulation seeds, not independent real-world samples**; the CIs describe variability of the simulator under the frozen design, not sampling error in a population of enterprises.

## 5. Factor A — producer deference

Quality @c40, write-back OFF: **0.764 → 0.396 → 0.237 → 0.237** for w = 0.0/0.3/0.7/0.9. Monotonic decline, **fully saturated by w ≈ 0.7**. **RQ3: supported, with the qualification that the response saturates early** — beyond w ≈ 0.7 additional deference changes nothing.

## 6. Factor B — decision write-back

ΔB (ON − OFF) at matched deference: **−0.527** at w=0.0; **+0.000** at w=0.7; **+0.001** at w=0.9. Write-back alone, with a producer that never defers, suppresses adaptation as completely as maximal deference does.

Mechanism verified directly in the n=10 run and unchanged here: with write-back ON, **45.3 %** of producer writes differ between w=0.0 and w=0.9, yet **0 %** of decisions change. Write-back copies constitute 50 % of readable state and pin the majority so firmly that fresh producer evidence never flips a decision.

## 7. Interaction

**+0.527** — strongly non-additive. Either channel alone saturates the effect; combining them adds nothing. **RQ2: supported** — both factors independently suppress adaptation, and they do not compose.

## 8. Static vs abrupt-shift

Covered in §3. The key point for the paper: absolute quality differences must never be read without the static comparator, because ~40 % of the raw c40 gap is present even with no truth change.

## 9. Comparison with the initial 10-seed run

| quantity | n=10 | n=30 | verdict |
|---|---|---|---|
| gap wb=OFF w=0.3 (+25) | 0.355 | 0.368 | replicated |
| gap wb=OFF w=0.7 (+25) | 0.522 | 0.527 | replicated |
| gap wb=ON w=0.0 (+25) | 0.507 | 0.527 | replicated |
| Factor A dose-response | 0.775→0.420→0.253→0.265 | 0.764→0.396→0.237→0.237 | replicated, cleaner monotonicity |
| Interaction | +0.510 | +0.527 | replicated |
| **Reference adaptation rate** | **10/10** | **20/30** | **corrected downward** |
| AOD / RR discrimination | none | none | replicated |

The effect estimates are stable to within ~0.02. The one substantive correction is the reference condition's adaptation rate, which the small run overstated.

## 10. RQ4 — negative result, unchanged

AOD = **1.000** in all seven conditions. RR = **0.938** in every write-back-OFF condition — including the reference, the only condition that adapts — and **0.978** in every write-back-ON condition. The provenance signals are constant across configurations that differ by 0.53 in outcome quality. They record that a feedback edge exists; they carry no information about whether harm is occurring. **RQ4: not supported.** AOD/RR are descriptive structural indicators only and must not be presented as harm detectors.

## 11. Threats to validity

Deterministic synthetic environment with no language model; binary decision task; majority-vote aggregation; **independent observation noise** (correlated noise implemented but untested — the largest outstanding threat, since the reference condition's recovery depends on accumulating independent evidence); abrupt total label flip is an extreme regime change; static entity population; producer deference and write-back are abstractions whose real-world rates are unmeasured; seeds are simulator replicates, not real-world samples.

## 12. Decision

# GO

RQ1, RQ2, RQ3 supported and replicated at 30 seeds with large, unanimous-direction effects and the mandatory static control passed. RQ4 is a clean negative and will be reported as such.

**Stage C2 (correlated noise) NOT started**, per the stop rule. It is the decisive robustness test: if the reference condition's recovery is an artifact of independent evidence accumulation, the effect may shrink or vanish under correlation. That must be run before any general claim.
