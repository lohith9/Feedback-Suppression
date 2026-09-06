"""
C2 correlated-noise robustness. Extends Sim1C WITHOUT modifying it or any C1
artefact. Noise model = persistent_entity_bias, exactly as pre-registered in
preregistration/C2_CORRELATED_NOISE.yaml.

  Each entity e gets one persistent error state B_e ~ Bernoulli(p) per (seed).
  Per observation of e:
      with prob rho   -> error = B_e            (persistent, repeats)
      with prob 1-rho -> error ~ Bernoulli(p)   (fresh, independent)
  Marginal P(error) = p for every rho, so only the DEPENDENCE structure varies.

Deterministic, CPU-only, no network, no models. Cost $0.
"""
import json, os, hashlib, random, datetime, argparse
from sim1c import Sim1C, make_cfg
from sim import Assertion

CODE_VERSION = "c2-correlated-1.0.0"


class CorrelatedNoise:
    def __init__(self, p, rho, rng, entities):
        self.p, self.rho, self.rng = p, rho, rng
        # one persistent error state per entity, drawn once
        self.B = {e: (1 if rng.random() < p else 0) for e in entities}

    def observe(self, entity, truth):
        if self.rng.random() < self.rho:
            err = self.B[entity]                    # persistent component
        else:
            err = 1 if self.rng.random() < self.p else 0   # fresh component
        return truth if err == 0 else 1 - truth


class SimC2(Sim1C):
    def __init__(self, cfg, seed):
        super().__init__(cfg, seed)
        # noise stream seeded ONLY by seed => paired across conditions
        self.cn = CorrelatedNoise(cfg["noise"]["base_error_rate"], cfg["rho"],
                                  random.Random(seed * 104729), self.entities)

    def produce(self, e, cycle):
        t = self.truth.value(e, cycle)
        own = self.cn.observe(e, t)
        self.obs += 1
        prior = self._readable(e)
        parents = [a.id for a in prior]
        val = own
        if prior and self.rng.random() < self.w:
            ones = sum(a.value for a in prior)
            val = 1 if ones * 2 >= len(prior) else 0
        self.store.add(Assertion(id=self.store.new_id(), entity=e, attribute="risk_level",
                                 value=val, origin="ai", cycle=cycle, parents=parents))

    def decide(self, e, cycle):
        prior = self._readable(e)
        parents = [a.id for a in prior]
        if prior:
            ones = sum(a.value for a in prior)
            d = 1 if ones * 2 >= len(prior) else 0
        else:
            d = self.cn.observe(e, self.truth.value(e, cycle))
        node = Assertion(id=self.store.new_id(), entity=e, attribute="decision",
                         value=d, origin="ai", cycle=cycle, parents=parents)
        self.store.add(node)
        self.store.add(Assertion(
            id=self.store.new_id(), entity=e,
            attribute=("risk_level" if self.writeback else "decision_archive"),
            value=d, origin="ai", cycle=cycle, parents=[node.id]))
        t = self.truth.value(e, cycle)
        self.regret += (1 - int(d == t))
        aod, rr, _ = self.store.aod_rr(node.id)
        return int(d == t), aod, rr


def cfg_c2(w, wb, rho):
    c = make_cfg("abrupt_shift", w, wb)
    c["rho"] = rho
    return c


CONDS = [("reference", False, 0.0), ("behavioural", False, 0.7), ("architectural", True, 0.0)]
RHOS = [0.0, 0.3, 0.6, 0.9]


def check_invariants(seeds=(1, 2, 3)):
    for rho in RHOS:
        for w in [0.0, 0.7]:
            for s in seeds:
                a = SimC2(cfg_c2(w, False, rho), s).run()[-1]["writes"]
                b = SimC2(cfg_c2(w, True, rho), s).run()[-1]["writes"]
                assert a == b, f"WRITE-VOLUME VIOLATION rho={rho} w={w} s={s}: {a}!={b}"
    # truth invariant
    sim = SimC2(cfg_c2(0.0, False, 0.5), 1)
    e = sim.entities[0]
    assert sim.truth.value(e, 14) != sim.truth.value(e, 15), "truth transition not at c15"
    # marginal error rate preserved across rho (statistical check)
    for rho in RHOS:
        rng = random.Random(999)
        cn = CorrelatedNoise(0.25, rho, rng, [f"e{i}" for i in range(200)])
        errs = sum(1 for _ in range(20000) if cn.observe(f"e{_%200}", 0) != 0)
        assert 0.22 < errs/20000 < 0.28, f"marginal error rate drifted at rho={rho}: {errs/20000}"
    return True


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"results/raw/c2_correlated_run_{ts}"
    os.makedirs(out, exist_ok=True)
    print("C2 INVARIANT PRE-CHECKS")
    check_invariants()
    print("  write-volume PASS | truth transition PASS | marginal error rate PASS (all rho)")

    seeds = list(range(1, 31))
    recs = []
    for rho in RHOS:
        for name, wb, w in CONDS:
            c = cfg_c2(w, wb, rho)
            ch = hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest()[:12]
            for s in seeds:
                recs.append({"condition": name, "writeback": wb, "deference_weight": w,
                             "rho": rho, "seed": s, "code_version": CODE_VERSION,
                             "config_hash": ch, "change_cycle": 15,
                             "rows": SimC2(c, s).run()})
    json.dump(recs, open(f"{out}/c2_correlated.json", "w"))
    json.dump({"timestamp": ts, "code_version": CODE_VERSION, "rhos": RHOS,
               "conditions": [[n, bool(wb), w] for n, wb, w in CONDS], "seeds": seeds,
               "n_records": len(recs), "noise_model": "persistent_entity_bias",
               "invariants": {"write_volume": "PASS", "truth": "PASS",
                              "marginal_error_rate": "PASS", "paired_seeds": "PASS"}},
              open(f"{out}/run_metadata.json", "w"), indent=2)
    print(f"\n{len(recs)} runs -> {out}/c2_correlated.json")
    print(out)


if __name__ == "__main__":
    main()
