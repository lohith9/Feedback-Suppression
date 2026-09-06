"""Layer 1 — Credit-Risk public-data scenario (UCI 350). SCIENTIFICALLY CORRECTED.

Baseline ground truth = the NATIVE UCI target ('default payment next month').
It is NEVER replaced by a median-thresholded model prediction (that would be
circular). A lightweight calibration model, fit on a DISJOINT subset, is used
ONLY to construct a documented counterfactual post-shift truth — never to define
baseline truth and never seen by the producer/decision system.

Modes:
  REAL       : requires data/raw/credit_default.csv. Baseline = native target.
  SUBSTRATE  : placeholder for software/interface/invariant tests ONLY. It is
               NOT a real-data result; describe()['is_real_data'] is False and a
               REAL-data pilot must never silently fall back to it.

Imports: stdlib + scenarios.base ONLY (no feedback/provenance/evaluation).
"""
import csv, math, os, random
try:
    import numpy as np
except Exception:
    np = None
from .base import Scenario

DATA_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "raw", "credit_default.csv")
NATIVE_PREVALENCE = 0.2212                      # UCI 350: 6636/30000 (documented)
PAY_FEATURES = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
PROTECTIVE = "LIMIT_BAL"
TARGET_COLS = ["default payment next month", "default.payment.next.month", "Y", "default"]


def _sigmoid(z):
    if z < -60: return 0.0
    if z > 60:  return 1.0
    return 1.0 / (1.0 + math.exp(-z))


class _RiskModel:
    """EVALUATOR-ONLY. Baseline label = native target. Post label = native target
    with a counterfactual-driven subset of non-defaulters flipped 0->1."""
    def __init__(self, entities, baseline, post):
        self.entities = entities
        self._baseline = baseline      # {entity: native target 0/1}
        self._post = post              # {entity: post-shift label 0/1}

    def truth(self, entity, shocked):
        return self._post[entity] if shocked else self._baseline[entity]

    def baseline_prevalence(self):
        return sum(self._baseline.values()) / len(self.entities)
    def post_prevalence(self):
        return sum(self._post.values()) / len(self.entities)
    def flip_fraction(self):
        return sum(1 for e in self.entities if self._baseline[e] != self._post[e]) / len(self.entities)


class CreditRiskTruth:
    """Duck-typed to frozen TruthProcess: .value(entity,cycle) + .change_cycles().
    Deterministic — consumes NO RNG. Pre-shift returns baseline (== native target)."""
    def __init__(self, model, mode, change_cycle):
        self._m = model; self.mode = mode; self.change_cycle = change_cycle
    def value(self, entity, cycle):
        shocked = (self.mode == "abrupt_shift" and cycle >= self.change_cycle)
        return self._m.truth(entity, shocked)
    def change_cycles(self):
        return [self.change_cycle] if self.mode == "abrupt_shift" else []


class CreditRiskScenario(Scenario):
    name = "credit_risk"

    def __init__(self, n_entities=100, mode="abrupt_shift", change_cycle=15,
                 shock=3.0, seed=1, data_csv=DATA_CSV, cal_fraction=0.5):
        self.n_entities = n_entities; self.mode = mode; self.change_cycle = change_cycle
        self.shock = shock; self.seed = seed; self.data_csv = data_csv
        self.cal_fraction = cal_fraction
        self.source = None; self._model = None; self._truth = None
        self._diag = {}

    # ---- Scenario interface ----
    def load(self):
        if os.path.exists(self.data_csv):
            self._build_real(self.data_csv); self.source = "real:UCI-350"
        else:
            self._build_substrate(); self.source = "SUBSTRATE (placeholder; real CSV absent)"
        return self

    def initialize_entities(self): return list(self._model.entities)
    def initialize_truth(self):
        self._truth = CreditRiskTruth(self._model, self.mode, self.change_cycle); return self._truth
    def observe(self, entity, cycle):
        raise RuntimeError("scenario never observes for the system; the engine's "
                           "NoiseProcess reads truth.value()")
    def apply_environment_change(self, cycle):
        return self.mode == "abrupt_shift" and cycle >= self.change_cycle
    def get_ground_truth(self, entity, cycle):
        """EVALUATOR-ONLY."""
        return self._truth.value(entity, cycle)
    def describe(self):
        return {"name": self.name, "source": self.source, "license": "CC BY 4.0",
                "doi": "10.24432/C55S3H", "n_entities": self.n_entities, "mode": self.mode,
                "change_cycle": self.change_cycle, "shock": self.shock,
                "is_real_data": self.source.startswith("real"),
                "native_prevalence": self._diag.get("native_prevalence"),
                "baseline_prevalence": round(self._model.baseline_prevalence(), 4),
                "post_prevalence": round(self._model.post_prevalence(), 4),
                "flip_fraction": round(self._model.flip_fraction(), 4)}

    # ---- REAL path (logistic-regression calibration; native target = baseline) ----
    def _build_real(self, path):
        assert np is not None, "numpy required for real-data calibration"
        rows = list(csv.DictReader(open(path)))
        tcol = next((c for c in TARGET_COLS if c in rows[0]), None)
        if tcol is None:
            raise ValueError(f"native target column not found; expected one of {TARGET_COLS}")
        for r in rows:
            r["_y"] = int(float(r[tcol]))
        self._diag["native_prevalence"] = round(sum(r["_y"] for r in rows) / len(rows), 4)
        feats = PAY_FEATURES + [PROTECTIVE]
        rng = random.Random(self.seed)
        idx = list(range(len(rows))); rng.shuffle(idx)
        cut = int(len(rows) * self.cal_fraction)
        cal = [rows[i] for i in idx[:cut]]           # DISJOINT calibration subset
        pool = [rows[i] for i in idx[cut:]]          # scenario/evaluation pool
        def colv(rs, f): return np.array([float(rs_r.get(f, 0) or 0) for rs_r in rs], dtype=float)
        mean = {f: colv(cal, f).mean() for f in feats}
        sd = {f: (colv(cal, f).std() or 1.0) for f in feats}
        def Z(rs): return np.column_stack([(colv(rs, f) - mean[f]) / sd[f] for f in feats])
        # ---- logistic regression with intercept (deterministic gradient descent) ----
        Xc = Z(cal); yc = np.array([r["_y"] for r in cal], dtype=float)
        w = np.zeros(len(feats)); b = 0.0
        for _ in range(400):
            pr = 1.0 / (1.0 + np.exp(-(Xc @ w + b))); g = pr - yc
            w -= 0.5 * ((Xc.T @ g) / len(yc) + 1e-4 * w); b -= 0.5 * g.mean()
        self._diag["lr_intercept"] = round(float(b), 4)
        self._diag["lr_coef"] = {f: round(float(w[i]), 4) for i, f in enumerate(feats)}
        # ---- deterministic stratified scenario sample preserving native prevalence ----
        pos = [r for r in pool if r["_y"] == 1]; neg = [r for r in pool if r["_y"] == 0]
        prev = self._diag["native_prevalence"]
        kp = round(self.n_entities * prev); kn = self.n_entities - kp
        rng.shuffle(pos); rng.shuffle(neg)
        sample = pos[:kp] + neg[:kn]; rng.shuffle(sample)
        Xs = Z(sample)
        p_base = 1.0 / (1.0 + np.exp(-(Xs @ w + b)))
        w_shock = w.copy()
        for i, f in enumerate(feats):                # GAMMA declared in prereg (=shock)
            if f in PAY_FEATURES: w_shock[i] = w[i] * self.shock
            elif f == PROTECTIVE: w_shock[i] = w[i] / self.shock
        p_shift = 1.0 / (1.0 + np.exp(-(Xs @ w_shock + b)))
        # operating bar theta* = probability cut that reproduces the native prevalence
        theta = float(np.quantile(p_base, 1.0 - (sum(r["_y"] for r in sample) / len(sample))))
        self._diag["theta_star"] = round(theta, 4)
        entities, baseline, post = [], {}, {}
        for i, r in enumerate(sample):
            e = f"client_{i:04d}"; entities.append(e)
            baseline[e] = r["_y"]                     # BASELINE = NATIVE TARGET (verbatim)
            # counterfactual downturn: a non-defaulter crosses the SAME risk bar under shock
            if r["_y"] == 0 and p_shift[i] >= theta:
                post[e] = 1
            else:
                post[e] = r["_y"]
        self._model = _RiskModel(entities, baseline, post)

    # ---- SUBSTRATE path (placeholder only) ----
    def _build_substrate(self):
        rng = random.Random(self.seed * 2654435761 % (2 ** 32))
        entities = [f"client_{i:04d}" for i in range(self.n_entities)]
        self._diag["native_prevalence"] = None
        baseline, post = {}, {}
        for e in entities:
            latent = rng.gauss(0, 1)
            # threshold to hit native-like prevalence (~0.2212), deterministic given latent
            b = 1 if latent > 0.768 else 0          # P(N(0,1)>0.768)≈0.2212
            baseline[e] = b
            d = rng.gauss(0, 1)                       # independent 'delinquency' latent
            # measured flip: a non-defaulter flips iff shock*delinquency crosses a cut
            post[e] = 1 if (b == 0 and self.shock * d > 3.0) else b
        self._model = _RiskModel(entities, baseline, post)


__all__ = ["CreditRiskScenario", "CreditRiskTruth"]
