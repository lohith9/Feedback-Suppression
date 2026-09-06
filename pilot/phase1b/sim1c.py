"""
Phase 1B CORRECTED simulator (Stage 1 re-run).

Two ORTHOGONAL factors (previously conflated into one "feedback" flag):
  Factor A  producer deference weight w in [0,1]
            probability the producer copies existing state instead of its own
            fresh observation.
  Factor B  decision write-back ON/OFF
            whether the decision is written back as READABLE authoritative
            state (attribute 'risk_level') or as an inert archival record
            (attribute 'decision_archive').

WRITE-VOLUME INVARIANT (directive SS19): both levels of Factor B write exactly
the same number of assertions. Write-back OFF still writes the decision, but to
a non-readable attribute. Therefore Factor B isolates the READABILITY/AUTHORITY
of the write-back, not the act of writing. This is what the previous design got
wrong (4800 vs 3200 writes).

Deterministic, CPU-only, no network, no models. Cost $0.
"""
import sys, os, json, hashlib, random, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import StateStore, Assertion
from truth_process import TruthProcess
from noise_process import NoiseProcess

CODE_VERSION = "phase1b-corrected-3.0.0"
READABLE = "risk_level"
INERT = "decision_archive"


class Sim1C:
    def __init__(self, cfg, seed):
        self.cfg, self.seed = cfg, seed
        self.rng = random.Random(seed)
        self.store = StateStore()
        self.entities = [f"e{i:04d}" for i in range(cfg["n_entities"])]
        # Paired design: truth and noise streams depend ONLY on seed, never on
        # the factors, so conditions see identical stochastic realisations.
        self.truth = TruthProcess(cfg["truth"], random.Random(seed * 7919), self.entities)
        self.noise = NoiseProcess(cfg["noise"], random.Random(seed * 104729))
        self.w = cfg["deference_weight"]
        self.writeback = cfg["decision_writeback"]
        self.obs = 0
        self.regret = 0.0

    def _readable(self, e):
        return [a for a in self.store.read_entity(e) if a.attribute == READABLE]

    def produce(self, e, cycle):
        t = self.truth.value(e, cycle)
        own = self.noise.observe(t, cycle)
        self.obs += 1
        prior = self._readable(e)
        parents = [a.id for a in prior]          # provenance always recorded
        val = own
        if prior and self.rng.random() < self.w:  # Factor A
            ones = sum(a.value for a in prior)
            val = 1 if ones * 2 >= len(prior) else 0
        self.store.add(Assertion(id=self.store.new_id(), entity=e, attribute=READABLE,
                                 value=val, origin="ai", cycle=cycle, parents=parents))

    def decide(self, e, cycle):
        prior = self._readable(e)
        parents = [a.id for a in prior]
        if prior:
            ones = sum(a.value for a in prior)
            d = 1 if ones * 2 >= len(prior) else 0
        else:
            d = self.noise.observe(self.truth.value(e, cycle), cycle)
        node = Assertion(id=self.store.new_id(), entity=e, attribute="decision",
                         value=d, origin="ai", cycle=cycle, parents=parents)
        self.store.add(node)
        # Factor B — identical write count either way; only readability differs.
        self.store.add(Assertion(
            id=self.store.new_id(), entity=e,
            attribute=(READABLE if self.writeback else INERT),
            value=d, origin="ai", cycle=cycle, parents=[node.id]))
        t = self.truth.value(e, cycle)
        self.regret += (1 - int(d == t))
        aod, rr, _ = self.store.aod_rr(node.id)
        return int(d == t), aod, rr

    def run(self):
        cfg, rows = self.cfg, []
        for cycle in range(1, cfg["cycles"] + 1):
            batch = self.rng.sample(self.entities, cfg["batch_size"])
            for e in batch:
                self.produce(e, cycle)
            c = a_ = r_ = 0.0
            for e in batch:
                cc, aod, rr = self.decide(e, cycle)
                c += cc; a_ += aod; r_ += rr
            n = len(batch)
            rows.append({"cycle": cycle, "quality": c / n, "AOD": a_ / n, "RR": r_ / n,
                         "writes": self.store._n, "observations": self.obs,
                         "cum_regret": self.regret})
        return rows


def make_cfg(truth_mode, w, writeback, cycles=40, change=15, noise_mode="independent"):
    return {"n_entities": 100, "cycles": cycles, "batch_size": 40,
            "deference_weight": w, "decision_writeback": writeback,
            "truth": {"mode": truth_mode, "change_cycle": change},
            "noise": {"mode": noise_mode, "base_error_rate": 0.25, "correlation": 0.0}}


def run_condition(truth_mode, w, wb, seeds):
    out = []
    for s in seeds:
        rows = Sim1C(make_cfg(truth_mode, w, wb), s).run()
        out.append({"truth_mode": truth_mode, "w": w, "writeback": wb, "seed": s,
                    "code_version": CODE_VERSION,
                    "config_hash": hashlib.sha256(
                        json.dumps(make_cfg(truth_mode, w, wb), sort_keys=True).encode()
                    ).hexdigest()[:12], "rows": rows})
    return out


def assert_write_invariant(seeds=(1, 2, 3)):
    """Directive SS19: experiment FAILS if write volume differs across Factor B."""
    for tm in ["static", "abrupt_shift"]:
        for w in [0.0, 0.7]:
            for s in seeds:
                a = Sim1C(make_cfg(tm, w, False), s).run()[-1]["writes"]
                b = Sim1C(make_cfg(tm, w, True), s).run()[-1]["writes"]
                assert a == b, f"WRITE-VOLUME INVARIANT VIOLATED {tm} w={w} s={s}: {a} != {b}"
    return True
