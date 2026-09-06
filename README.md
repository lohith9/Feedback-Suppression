# When AI Writes the Record: Feedback Suppression of Adaptation in Structured State

A reproducible research framework for studying the feedback that arises when
AI-generated **structured state** becomes machine-readable evidence for
subsequent automated decisions.

> ⚠️ **This repository is a research artifact, not a production safety,
> governance, credit-scoring, or harm-detection system.** It characterises a
> phenomenon in a controlled simulator. It makes no claim about deployed
> enterprise systems or language-model agents, and nothing here should be used
> to score, rank, or make decisions about real people.

---

## 1. Purpose
When an AI system writes a typed value into a system of record (a risk field, a
severity, a classification) and a later automated decision reads that value back
as evidence, a feedback loop closes **without any retraining**. This project asks
a narrow question: under **fixed decision policies with no parameter updates or
retraining**, does that feedback suppress the system's ability to **recover after
the underlying truth changes** — and through which channels?

## 2. What the framework studies
Feedback carried by AI-written *typed structured state*, with recovery after an
exogenous truth change as the measured outcome. It separates two channels —
**behavioural producer deference** (Factor A) and **architectural readable
write-back** (Factor B) — under matched write volume, and asks whether simple
provenance signals can tell harmful feedback from benign.

## 3. Architecture (seven layers)
The system under test is separated from **read-only** research instrumentation:

1. **Scenario / Data** — entities, noisy observations, evaluator-only truth, environmental change.
2. **System under test** — producer → structured state store → aggregator → decision → write-back.
3. **Feedback mechanisms** — Factor A (deference) and Factor B (readable write-back).
4. **Read-only evaluation / instrumentation** — provenance, oracle, metrics; never alters state, randomness, or control flow (verified: 70 conditions bit-identical instrument on/off).
5. **Experiment controller** — one shared controller, paired seeds, invariant checks.
6. **Evaluation** — primary metrics + descriptive-only indicators.
7. **Reproducible output** — immutable raw records; 780 runs reproduce bit-exactly.

See `ARCHITECTURE_DESIGN.md` and Figure 1 in the paper.

## 4. Research questions
- **Primary:** does fixed-policy structured-state feedback suppress recovery after a truth change, and via which channels?
- **RQ-A** channel separation · **RQ-B** dose-response · **RQ-C** robustness to temporal observation dependence · **RQ-D** can provenance signals detect harm? *(negative)* · **RQ-E** does it reproduce under a realistic partial real-data shift? *(boundary)*

## 5. Experiments
- **C1 — controlled synthetic reference:** 7 conditions × 2 truth regimes × 30 seeds = **420 runs**. Establishes adaptation suppression and the Factor A/B separation.
- **C2 — correlated-noise robustness:** 3 conditions × 4 correlation levels × 30 seeds = **360 runs**. Effect retained 92–94% at ρ=0.9.
- **UCI external-grounding boundary:** UCI Default of Credit Card Clients; native target as baseline truth; a realistic partial counterfactual shift. The adaptation-specific effect attenuates to ≈0 — reported as an **external-validity boundary**, not a positive result.

**Total: 780 runs (C1+C2).**

## 6. Reproduction
```bash
# (1) VERIFY EXISTING C1/C2 RESULTS — canonical, bit-exact (all 780 published runs):
python3 reproduce.py --scenario synthetic --experiment c1   # -> 420/420 exact
python3 reproduce.py --scenario synthetic --experiment c2   # -> 360/360 exact

# (2) AUDIT EXISTING V3 RESULTS — recompute the severity result from immutable raw:
python3 audit/v3/audit_recompute.py

# (3) RE-RUN V3 EXPERIMENT — optional; writes a NEW timestamped dir, never overwrites:
#     python3 run_severity_confirmatory.py     (the existing run is the artifact of record)
```
Full regeneration commands (runners, analysis, figures) are in `REPRODUCIBILITY.md`.
Requirements: Python 3.10+, `matplotlib` (figures only), `numpy`. CPU only.

**Repository layout:** `src/` (seven-layer architecture), `pilot/` (frozen C1/C2 engine + immutable raw runs), `tests/` (reproducibility + non-interference invariants), `audit/v3/` (independent V3 recompute), `preregistration/`, `results/`, `data/`.

## 7. Expected results
- Reference adapts 20/30 seeds; every feedback configuration 0/30.
- Paired adaptation gaps 0.368–0.527 (d ≈ 5.0–5.3).
- Factor A dose-response 0.764 / 0.396 / 0.237 / 0.237; ΔB = −0.527 / +0.000 / +0.001; interaction +0.527; 45.3% of producer writes differ while 0% of decisions change.
- C2 retention 94% / 92% at ρ=0.9.
- AOD = 1.000; RR = 0.938 / 0.978 (provenance signals do **not** distinguish harmful from benign — negative result).
- UCI adaptation-specific effect ≈ 0.000 / 0.025 (boundary).

`reproduce.py` verifies these byte-for-byte against the immutable raw records.

## 7b. Severity extension (V3)
A **pre-registered follow-up** (`preregistration/SHIFT_SEVERITY_V3.yaml`, SHA-256
`2301d948…`) characterizes how the adaptation-specific penalty scales with the
severity σ of the truth change (σ = fraction of entities whose truth flips).
- **1050 runs over 50 independent seeds** (3 conditions × [1 static + 6 σ] × 50); severity grid **{0, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00}**.
- The adaptation-specific penalty **rises approximately linearly** with σ: average slope **≈ +0.300, 95% CI [+0.258, +0.343]**.
- **No evidence of a difference** between the behavioural and architectural channels (arch − beh slope ≈ −0.019, 95% CI [−0.042, +0.005]); the study is not powered to establish equivalence.
- At full inversion (σ=1) the penalty **converges to the C1 value (~0.30)** — convergent validity, not bit-exact replication.
- Raw: `results/raw/severity_run_20260829_190638/`. Recompute independently: `python3 audit/v3/audit_recompute.py`.

> **V3 characterizes the severity-response of the previously identified structured-state feedback effect within the controlled simulator; it is not presented as a discovery of severity dependence or as evidence about deployed or LLM-based systems.** **1050 runs are not 1050 independent samples; inference uses 50 independent seeds.**

**V3 is not part of the frozen 6-page ACDSA paper** (page limit; least-novel piece).

## 8. Cost
**$0.00.** No paid API, hosted model, cloud instance, GPU, paid dataset, or
account. The simulator contains no language model. The entire study runs on a
laptop in under a minute.

## 9. Dataset (UCI) instructions
The UCI boundary experiment uses the **Default of Credit Card Clients** dataset
(UCI ID 350; Yeh & Lien 2009; CC BY 4.0).

- **Source:** https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients
- **Citation:** I-C. Yeh and C-H. Lien, *Expert Systems with Applications*, 36(2):2473–2480, 2009.
- **Checksums** of the copy used:
  - `credit_default.xls` SHA-256 `30c6be3abd8dcfd3e6096c828bad8c2f011238620f5369220bd60cfc82700933`
  - `credit_default.csv` SHA-256 `eeaaa5addd59a2c56e82cbfca996f37ad98714c0237f1a3cbc8d7e973102966d`
- The UCI raw data is **NOT distributed in this repository** (it is git-ignored). Download it yourself from the UCI link above, place it in `data/raw/`, and verify it against the checksums above.
- **The C1 and C2 experiments (the paper's core evidence, all 780 runs) are fully reproducible WITHOUT the UCI dataset** — `reproduce.py` needs no external data. The UCI dataset is required only to re-run the optional external-validity boundary analysis.

**Important distinction:** the UCI data is an empirical *substrate* only. The
feedback loop is **introduced by our simulator**; the dataset itself contains no
AI feedback loop. The native default label is used verbatim as baseline truth.

## 10. Limitations
Synthetic controlled environment; no language model in C1/C2; binary task with
majority-vote aggregation; severe synthetic inversion in C1/C2; the UCI partial
shift did **not** reproduce the adaptation-specific effect (external
generalisation not established); provenance indicators are descriptive only (not
harm detectors); simulator seeds are not organisations; systematically misleading
observations untested; no production validation. See the paper's Limitations and
Threats sections.

## 11. Citation
This is a research artifact accompanying a manuscript **submitted to ACDSA 2027**
(under review; not yet published, and with no assigned DOI). See `CITATION.cff`.
Please also cite the UCI dataset (Yeh & Lien 2009) if you use the credit-risk
scenario.

## 12. Use of generative AI
Generative AI (Anthropic Claude) assisted with literature searching/screening,
experiment design, simulator and analysis code, statistical analysis, figure
generation, and manuscript drafting/editing. All research questions,
methodological decisions, interpretations, and final claims were reviewed and
approved by the human author, who takes full responsibility. **No AI system is an
author of this work.** All reported values derive from executed code whose raw
outputs are included.

## 13. License
- **Source code** (`src/`, `pilot/`, `tests/`, `reproduce.py`, runners): **MIT** — see `LICENSE`.
- **Research content** (manuscript, figures, documentation, reports, reproducibility docs, pre-registrations, generated result records): **CC BY 4.0** — see `LICENSE-CONTENT.md`.
- **UCI dataset**: third-party material under **its own CC BY 4.0** terms; **not relicensed and not distributed** here — see `data/README.md`.

(The published IEEE version, if accepted, is under IEEE copyright; CC BY 4.0 here covers the author's repository copy.)

## 14. Status
The manuscript is **scientifically and editorially frozen** (6-page IEEE
conference paper, official IEEEtran). This repository packages the code, data
pointers, and reproduction path. It is a research artifact for study and
reproduction only.
