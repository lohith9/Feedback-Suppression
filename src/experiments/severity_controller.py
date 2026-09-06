"""Severity-study controller (Layer 5, additive).

Runs one severity condition by REUSING the frozen Sim1C produce/decide/run loop
and swapping ONLY the truth process for PartialShiftTruth — the identical pattern
used by run_credit_condition. No frozen engine file is modified. The agent RNG
(Random(seed)) and noise RNG (Random(seed*104729)) are constructed exactly as in
Sim1C; the severity truth uses the truth RNG (Random(seed*7919)) only.

Frozen design: preregistration/SHIFT_SEVERITY_V3.yaml.
Confirmatory execution (50 seeds / 1050 runs) is NOT performed here.
"""
import random
from .. import _engine_path  # noqa: F401  (bootstraps path to the frozen engine)
from sim1c import Sim1C, make_cfg
from sim import StateStore
from noise_process import NoiseProcess
from ..scenarios.partial_shift import PartialShiftTruth
from .controller import _Sim1C_NoInstrument

CODE_VERSION = "severity-v3.0.0"

# Primary conditions (M8). Combined A+B is optional secondary, not included here.
SEVERITY_CONDITIONS = {
    "reference":     (False, 0.0),   # (writeback, deference_weight)
    "behavioural":   (False, 0.7),   # Factor A only
    "architectural": (True,  0.0),   # Factor B only
}
SEVERITY_SIGMAS = [0.00, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00]


def _truth_cfg(regime, sigma, change):
    # static regime == partial_shift with sigma=0 (balanced base, no flip)  (M3/I4)
    s = 0.0 if regime == "static" else float(sigma)
    return {"mode": "partial_shift", "sigma": s, "change_cycle": int(change)}


def run_severity_condition(condition, sigma, regime, seed,
                           n_entities=100, cycles=40, change=15, instrument=True):
    """Return (rows, truth_object) for one run. `regime` in {'static','partial_shift'}.
    For regime='static', sigma is ignored (treated as 0)."""
    if condition not in SEVERITY_CONDITIONS:
        raise KeyError(condition)
    writeback, w = SEVERITY_CONDITIONS[condition]
    base_cls = Sim1C if instrument else _Sim1C_NoInstrument

    class _SeveritySim(base_cls):
        def __init__(self, cfg, seed):
            # Reconstruct __init__ exactly like Sim1C, swapping ONLY the truth
            # process (mirrors run_credit_condition's _CreditSim).
            self.cfg, self.seed = cfg, seed
            self.rng = random.Random(seed)                       # AGENT stream (untouched)
            self.store = StateStore()
            self.entities = [f"e{i:04d}" for i in range(cfg["n_entities"])]
            self.truth = PartialShiftTruth(cfg["truth"],
                                           random.Random(seed * 7919),  # TRUTH stream only
                                           self.entities)
            self.noise = NoiseProcess(cfg["noise"], random.Random(seed * 104729))  # NOISE stream (untouched)
            self.w = cfg["deference_weight"]
            self.writeback = cfg["decision_writeback"]
            self.obs = 0
            self.regret = 0.0

    cfg = make_cfg("static", w, writeback, cycles=cycles, change=change)
    cfg["n_entities"] = n_entities
    cfg["truth"] = _truth_cfg(regime, sigma, change)
    sim = _SeveritySim(cfg, seed)
    rows = sim.run()
    return rows, sim.truth


__all__ = ["run_severity_condition", "SEVERITY_CONDITIONS", "SEVERITY_SIGMAS", "CODE_VERSION"]
