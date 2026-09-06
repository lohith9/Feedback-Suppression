"""Layer 5 — shared experiment controller. No code forks per condition.

Canonical engines are the FROZEN, validated Sim1C (C1) and SimC2 (C2). The
controller composes them behind one API and adds an `instrument` switch used
only by the non-interference test. Equivalence to the 780 published runs is
proven by tests/test_reference_regression.py.
"""
from .. import _engine_path  # noqa: F401
from sim1c import Sim1C, make_cfg
from sim_c2 import SimC2, cfg_c2, CONDS as C2_CONDS, RHOS as C2_RHOS


# ---- instrumentation toggle (Layer-4 non-interference demonstration) --------
class _Sim1C_NoInstrument(Sim1C):
    """Identical to Sim1C but with provenance instrumentation (aod_rr) disabled.
    aod_rr consumes NO system RNG and mutates NO state, so decisions/writes/
    quality MUST be identical. If they ever differ, instrumentation is leaking —
    the test would catch it."""
    def decide(self, e, cycle):
        prior = self._readable(e)
        parents = [a.id for a in prior]
        if prior:
            ones = sum(a.value for a in prior)
            d = 1 if ones * 2 >= len(prior) else 0
        else:
            d = self.noise.observe(self.truth.value(e, cycle), cycle)
        from sim import Assertion
        node = Assertion(id=self.store.new_id(), entity=e, attribute="decision",
                         value=d, origin="ai", cycle=cycle, parents=parents)
        self.store.add(node)
        self.store.add(Assertion(
            id=self.store.new_id(), entity=e,
            attribute=("risk_level" if self.writeback else "decision_archive"),
            value=d, origin="ai", cycle=cycle, parents=[node.id]))
        t = self.truth.value(e, cycle)
        self.regret += (1 - int(d == t))
        return int(d == t), 0.0, 0.0          # <-- no aod_rr call (instrumentation off)


def run_c1_condition(truth_mode, w, writeback, seed, instrument=True):
    engine = (Sim1C if instrument else _Sim1C_NoInstrument)(
        make_cfg(truth_mode, w, writeback), seed)
    return engine.run()


def run_c2_condition(condition_name, w, writeback, rho, seed):
    return SimC2(cfg_c2(w, writeback, rho), seed).run()


# C1 factor grid (frozen)
C1_CONDITIONS = [(False, 0.0), (False, 0.3), (False, 0.7), (False, 0.9),
                 (True, 0.0), (True, 0.7), (True, 0.9)]
C1_REGIMES = ["static", "abrupt_shift"]
__all__ = ["run_c1_condition", "run_c2_condition", "C1_CONDITIONS", "C1_REGIMES",
           "C2_CONDS", "C2_RHOS"]


# ---- credit-risk scenario runner (reuses the frozen Sim1C mechanism) -------
def run_credit_condition(scenario, w, writeback, seed, instrument=True):
    """Run one credit-risk condition. Reuses the EXACT frozen Sim1C produce/decide/
    run loop; only the truth-generating process is swapped for the scenario's
    (evaluator-only) CreditRiskTruth. Mechanism, write-invariant, and RNG order are
    therefore identical to C1 by construction."""
    from sim1c import Sim1C, make_cfg
    base = Sim1C if instrument else _Sim1C_NoInstrument

    class _CreditSim(base):
        def __init__(self, cfg, seed, scen):
            import random as _r
            self.cfg, self.seed = cfg, seed
            self.rng = _r.Random(seed)
            from sim import StateStore
            self.store = StateStore()
            self.entities = scen.initialize_entities()
            self.truth = scen.initialize_truth()          # duck-typed TruthProcess
            from noise_process import NoiseProcess
            self.noise = NoiseProcess(cfg["noise"], _r.Random(seed * 104729))
            self.w = cfg["deference_weight"]
            self.writeback = cfg["decision_writeback"]
            self.obs = 0
            self.regret = 0.0

    cfg = make_cfg(scenario.mode, w, writeback,
                   cycles=40, change=scenario.change_cycle)
    cfg["n_entities"] = scenario.n_entities
    return _CreditSim(cfg, seed, scenario).run()
