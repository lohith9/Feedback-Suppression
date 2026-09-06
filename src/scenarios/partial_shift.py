"""PartialShiftTruth — evaluator-only ground truth for the shift-severity study.

Frozen design: preregistration/SHIFT_SEVERITY_V3.yaml (M1-M7).

Properties (all enforced by tests/test_severity_invariants.py):
  * Exactly-balanced base: N/2 zeros + N/2 ones, assigned to a truth-RNG shuffle
    of the entities. Neutralises the engine's tie-break-to-1 asymmetry (M1).
  * Nested, balanced flip subset (M2): ONE truth-RNG shuffle of the zero-entities
    and ONE of the one-entities; severity sigma flips the first k of each, where
    k = round(sigma * N/2). |S| = 2k, sigma = 2k/N. Balanced => prevalence
    preserved exactly. Prefix => nested across sigma.
  * Uses ONLY the passed (truth) RNG. Never touches the agent or noise RNG streams.
  * Duck-typed to the frozen TruthProcess: exposes .value(entity, cycle) and
    .change_cycles(); the frozen Sim1C uses only .value().

This module does NOT modify any frozen engine file. It is consumed by
src/experiments/severity_controller.py via a Sim1C subclass, exactly as the
credit-risk scenario is (see run_credit_condition).
"""


class PartialShiftTruth:
    def __init__(self, cfg, rng, entities):
        self.cfg = cfg
        self.change = int(cfg.get("change_cycle", 15))
        self.sigma = float(cfg["sigma"])
        N = len(entities)
        if N % 2 != 0:
            raise ValueError("partial_shift requires even N for an exactly-balanced base")
        half = N // 2

        # --- M1: exactly-balanced base on a deterministic truth-RNG shuffle -----
        perm = list(entities)
        rng.shuffle(perm)                         # consumes truth RNG only
        self.base = {e: (0 if i < half else 1) for i, e in enumerate(perm)}

        # --- M2: nested balanced flip subset -----------------------------------
        zeros = [e for e in perm if self.base[e] == 0]
        ones = [e for e in perm if self.base[e] == 1]
        rng.shuffle(zeros)                        # fixed per seed, independent of sigma
        rng.shuffle(ones)
        k = round(self.sigma * half)              # sigma on 0.02 lattice -> integer k
        if not (0 <= k <= half):
            raise ValueError(f"infeasible sigma={self.sigma} for N={N} (k={k})")
        self.k = k
        self._zeros_order = zeros                 # exposed for the nesting invariant test
        self._ones_order = ones
        self.flip = set(zeros[:k]) | set(ones[:k])
        self.sigma_measured = len(self.flip) / N  # must equal declared sigma (I1)

    # ---- frozen-TruthProcess-compatible interface --------------------------------
    def value(self, entity, cycle):
        v = self.base[entity]
        if cycle >= self.change and entity in self.flip:
            return 1 - v
        return v

    def change_cycles(self):
        return [self.change] if self.sigma > 0 else []

    # ---- helpers for invariant tests (read-only) --------------------------------
    def flip_set(self):
        return set(self.flip)

    def prevalence(self, cycle):
        vals = [self.value(e, cycle) for e in self.base]
        return sum(vals) / len(vals)
