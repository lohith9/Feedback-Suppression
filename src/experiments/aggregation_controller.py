"""V4 aggregation-rule ablation controller (Layer 5, additive).

Frozen design: preregistration/AGGREGATION_ABLATION_V4.yaml.
Reuses the frozen Sim1C engine. The subclass changes ONLY how readable
assertions are selected and weighted when the producer defers (Factor A) and
when the decision is formed. RNG call order, write pattern and write volume are
unchanged. With aggregator "CUM" it must reproduce the published C1 runs
bit-exactly (invariant I1).
"""
from .. import _engine_path  # noqa: F401
from sim1c import Sim1C, make_cfg, READABLE, INERT
from sim import Assertion

CODE_VERSION = "aggregation-v4.0.0"
AGGREGATORS = ["CUM", "WIN5", "WIN10", "LWW", "EXP"]
CONDITIONS = {"REF": (False, 0.0), "A": (False, 0.7), "B": (True, 0.0), "AB": (True, 0.7)}


class AggSim(Sim1C):
    def __init__(self, cfg, seed, aggregator):
        super().__init__(cfg, seed)
        if aggregator not in AGGREGATORS:
            raise KeyError(aggregator)
        self.agg = aggregator
        self._t = 0

    # which readable assertions count
    def _select(self, prior):
        if self.agg in ("CUM", "EXP"):
            return prior
        if self.agg == "WIN5":
            return [a for a in prior if a.cycle > self._t - 5]
        if self.agg == "WIN10":
            return [a for a in prior if a.cycle > self._t - 10]
        if self.agg == "LWW":
            return prior[-1:]
        raise KeyError(self.agg)

    # vote over the selected assertions (ties -> 1, as in the frozen engine)
    def _vote(self, sel):
        if self.agg == "EXP":
            wts = [0.5 ** ((self._t - a.cycle) / 3.0) for a in sel]
            ones = sum(w for w, a in zip(wts, sel) if a.value == 1)
            return 1 if ones * 2 >= sum(wts) else 0
        ones = sum(a.value for a in sel)
        return 1 if ones * 2 >= len(sel) else 0

    def produce(self, e, cycle):
        self._t = cycle
        t = self.truth.value(e, cycle)
        own = self.noise.observe(t, cycle)
        self.obs += 1
        prior = self._readable(e)
        parents = [a.id for a in prior]
        sel = self._select(prior)
        val = own
        if sel and self.rng.random() < self.w:            # Factor A
            val = self._vote(sel)
        self.store.add(Assertion(id=self.store.new_id(), entity=e, attribute=READABLE,
                                 value=val, origin="ai", cycle=cycle, parents=parents))

    def decide(self, e, cycle):
        self._t = cycle
        prior = self._readable(e)
        parents = [a.id for a in prior]
        sel = self._select(prior)
        if sel:
            d = self._vote(sel)
        else:
            d = self.noise.observe(self.truth.value(e, cycle), cycle)
        node = Assertion(id=self.store.new_id(), entity=e, attribute="decision",
                         value=d, origin="ai", cycle=cycle, parents=parents)
        self.store.add(node)
        self.store.add(Assertion(id=self.store.new_id(), entity=e,
                                 attribute=(READABLE if self.writeback else INERT),
                                 value=d, origin="ai", cycle=cycle, parents=[node.id]))
        t = self.truth.value(e, cycle)
        self.regret += (1 - int(d == t))
        aod, rr, _ = self.store.aod_rr(node.id)
        return int(d == t), aod, rr


def run_agg_condition(aggregator, regime, writeback, w, seed):
    return AggSim(make_cfg(regime, w, writeback), seed, aggregator).run()


__all__ = ["AggSim", "run_agg_condition", "AGGREGATORS", "CONDITIONS", "CODE_VERSION"]
