# CREDIT_RISK_MAPPING.md
### Explicit dataset → scenario mapping (16 Aug 2026)
### Scientific framing (mandatory): the UCI dataset does NOT contain an AI feedback loop. It is an empirical substrate; the feedback mechanism is introduced by our simulator.

## Flow
```
client features + payment history   (real data)
        ↓  fit a logistic risk model P(default | features)         [evaluator-only]
latent risk state per client        (ground truth, evaluator-only)
        ↓  producer observes it with noise                          [system under test]
structured risk state: risk_level   (typed field, our mechanism)
        ↓  decision cycle reads state, decides, writes back         [system under test]
next cycle …                        (feedback introduced HERE, by us)
```

## Field-by-field

| Source field(s) | Scenario concept | Transformation | Reason | Affects ground truth? | Observable by producer? | Evaluator-only? |
|---|---|---|---|---|---|---|
| `default payment next month` | anchor for latent risk | used to fit the risk model coefficients | native target grounds the risk relationship | **yes (anchor)** | no | **yes** |
| `LIMIT_BAL, PAY_0..PAY_6, BILL_AMT*, PAY_AMT*` | risk-predictive features | standardised; fed to logistic model | real feature→default structure | via the fitted model | no (features shape truth, not observed directly) | yes |
| `SEX, EDUCATION, MARRIAGE, AGE` | demographic context | retained in fit, **excluded from the shift** | avoid building a shift on protected attributes | via fit only | no | yes |
| fitted `P(default|x)` | per-client latent risk | threshold at median → binary `high_risk` | binary label comparable to C1/C2; balanced | **yes** | no | yes |
| noisy read of `high_risk` | producer observation | `observe()` flips with prob = noise | this is the only thing the system sees | n/a | **yes** | no |

## Ground-truth firewall
- The logistic coefficients, the per-client `P(default)`, the threshold, and the regime are held in the scenario's **evaluator-only** state.
- The producer receives ONLY `observe(entity, cycle)` — a noisy binary. The decision reads ONLY structured state. Neither can reach `get_ground_truth()`.
- `tests/test_credit_risk_scenario.py` asserts this firewall (no oracle attribute is reachable from the system path).

## What is empirical vs simulated
- **Empirical:** feature distributions, the feature→default relationship (fitted coefficients), class balance.
- **Simulated (by us):** the repeated decision cycles, observation noise, producer deference, decision write-back, and the regime shift. These are our mechanism, not properties of the data.

---

## CORRECTION (16 Aug 2026) — baseline truth is the NATIVE target
The earlier draft defined `high_risk` via a median threshold on a fitted probability. That is circular (fitting a model, then evaluating against its own thresholded output). **Corrected:** in REAL mode `baseline_truth = native "default payment next month"` verbatim; the fitted model is used ONLY to build the counterfactual post-shift labels, on a disjoint subset, and is never seen by the system. See `CREDIT_RISK_SCIENTIFIC_VALIDATION.md`.
