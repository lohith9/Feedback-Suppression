"""
AI-Origin State Lineage — Phase 0 deterministic smoke test.

Scope (per CLAUDE_CODE_BRIEF.md): simulator + provenance graph + arms A1/A3/A9 only.
No models. No network. No paid resources. Pure CPU, seeded, deterministic.

System model:
    Producer -> structured state (typed assertion) -> Decision AI reads state
             -> decision (itself written back as state) -> next cycle

Provenance: each assertion records its parents (the assertions read to produce it).
Ancestry = why-provenance closure, restricted to AI-origin nodes for our metrics.

Metrics (see RESEARCH_PROPOSAL.md §6):
    AOD = |ancestry nodes that are AI-origin| / |ancestry|
    RR  = |ancestry nodes that are AI-origin AND concern the same entity+attribute|
          / |ancestry|                      (self-reference, not merely AI-origin)

The two quality signals deliberately differ, and this is the crux of the study:
    * conventional monitor = accuracy on a FIXED CLEAN HOLDOUT (fresh entities,
      no accumulated state). This is what an operator actually watches. It has no
      access to accumulated production state, so it is structurally blind to
      state contamination. This is realistic, not rigged.
    * true live quality = accuracy on live entities vs simulator ground truth.
      The operator CANNOT see this without labels. Our provenance metrics are
      label-free, which is the whole value proposition.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set
import argparse
import json
import hashlib
import random
import os


# --------------------------------------------------------------------------
# Provenance primitives
# --------------------------------------------------------------------------

@dataclass
class Assertion:
    """One typed value written into structured enterprise state."""
    id: str
    entity: str
    attribute: str
    value: int
    origin: str              # "ai" | "human"
    cycle: int
    parents: List[str] = field(default_factory=list)
    human_approved: bool = False   # laundering event marker (measured, not claimed)


class StateStore:
    """Structured state + why-provenance graph."""

    def __init__(self) -> None:
        self.assertions: Dict[str, Assertion] = {}
        self.by_entity: Dict[str, List[str]] = {}
        self._n = 0

    def new_id(self) -> str:
        self._n += 1
        return f"a{self._n:06d}"

    def add(self, a: Assertion) -> None:
        self.assertions[a.id] = a
        self.by_entity.setdefault(a.entity, []).append(a.id)

    def read_entity(self, entity: str) -> List[Assertion]:
        return [self.assertions[i] for i in self.by_entity.get(entity, [])]

    def ancestry(self, aid: str) -> Set[str]:
        """why-provenance closure (excluding the node itself)."""
        seen: Set[str] = set()
        stack = list(self.assertions[aid].parents)
        while stack:
            cur = stack.pop()
            if cur in seen or cur not in self.assertions:
                continue
            seen.add(cur)
            stack.extend(self.assertions[cur].parents)
        return seen

    def aod_rr(self, aid: str):
        """
        AOD = AI-Origin Dependence: AI-origin share of why-provenance ancestry.

        RR = Reinforcement (echo) Ratio: share of ancestry that is AI-origin AND
        was itself derived from pre-existing state (has parents), rather than
        being a fresh grounded observation of the world.

        NOTE (smoke-test finding): the original definition keyed self-reference
        on matching `attribute`, which is degenerate here -- a decision node's
        attribute never equals its evidence's attribute, so RR was identically
        0. Keying on "same entity" instead is also degenerate, since all
        ancestry of a decision concerns one entity, making RR == AOD. The
        meaningful quantity is *recycled vs grounded evidence*: an assertion
        with no parents is anchored in a fresh observation; one with parents was
        pulled toward existing authoritative state. RR therefore measures how
        much of the decision's support is the system re-reading its own output.
        """
        anc = self.ancestry(aid)
        if not anc:
            return 0.0, 0.0, 0
        ai = [n for n in anc if self.assertions[n].origin == "ai"]
        echoed = [n for n in ai if self.assertions[n].parents]
        return len(ai) / len(anc), len(echoed) / len(anc), len(anc)

    def max_depth(self, aid: str) -> int:
        """Propagation depth (established lineage term)."""
        depth = 0
        frontier = list(self.assertions[aid].parents)
        seen: Set[str] = set()
        while frontier:
            depth += 1
            nxt: List[str] = []
            for n in frontier:
                if n in seen or n not in self.assertions:
                    continue
                seen.add(n)
                nxt.extend(self.assertions[n].parents)
            frontier = nxt
            if depth > 100:
                break
        return depth


# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------

class Sim:
    def __init__(self, cfg: dict, seed: int) -> None:
        self.cfg = cfg
        self.rng = random.Random(seed)
        self.store = StateStore()
        self.n_entities = cfg["n_entities"]
        # Ground truth: known to the evaluator ONLY. Agents never see it.
        self.truth = {f"e{i:04d}": self.rng.randint(0, 1) for i in range(self.n_entities)}
        self.holdout_id = 0

    # -- agents -----------------------------------------------------------

    def _observe(self, entity: str, noise: float) -> int:
        """Noisy observation of ground truth."""
        t = self.truth[entity]
        return t if self.rng.random() > noise else 1 - t

    def producer_write(self, entity: str, cycle: int) -> Assertion:
        """Producer writes an assertion into structured state."""
        cfg = self.cfg
        origin = "ai" if self.rng.random() < cfg["ai_write_fraction"] else "human"
        noise = cfg["ai_noise"] if origin == "ai" else cfg["human_noise"]
        obs = self._observe(entity, noise)

        parents: List[str] = []
        value = obs

        if cfg["feedback"]:
            prior = [a for a in self.store.read_entity(entity)
                     if a.attribute == "risk_level"]
            if prior:
                parents = [a.id for a in prior]
                # Confirmation pull: the agent weights existing authoritative
                # state instead of its own fresh observation.
                ones = sum(a.value for a in prior)
                majority = 1 if ones * 2 >= len(prior) else 0
                if self.rng.random() < cfg["confirmation_weight"]:
                    value = majority

        a = Assertion(
            id=self.store.new_id(), entity=entity, attribute="risk_level",
            value=value, origin=origin, cycle=cycle, parents=parents,
        )
        # Human laundering: approval relabels origin as human-approved.
        if origin == "ai" and self.rng.random() < cfg["laundering_rate"]:
            a.human_approved = True
        self.store.add(a)
        return a

    def decide(self, entity: str, cycle: int):
        """Decision AI reads state, decides, and writes the decision back as state."""
        prior = [a for a in self.store.read_entity(entity)
                 if a.attribute == "risk_level"]
        parents = [a.id for a in prior]
        if prior:
            ones = sum(a.value for a in prior)
            decision = 1 if ones * 2 >= len(prior) else 0
        else:
            decision = self._observe(entity, self.cfg["ai_noise"])

        d = Assertion(
            id=self.store.new_id(), entity=entity, attribute="decision",
            value=decision, origin="ai", cycle=cycle, parents=parents,
        )
        self.store.add(d)

        # Close the loop (system model §5): the decision itself becomes new
        # authoritative structured state that later cycles read as evidence.
        # Without this the "Decision -> New Structured State -> Next Cycle"
        # edge is missing and no feedback can occur.
        if self.cfg["feedback"] and self.cfg.get("decision_writes_back", True):
            fb = Assertion(
                id=self.store.new_id(), entity=entity, attribute="risk_level",
                value=decision, origin="ai", cycle=cycle, parents=[d.id],
            )
            self.store.add(fb)
        correct = int(decision == self.truth[entity])
        aod, rr, anc = self.store.aod_rr(d.id)
        depth = self.store.max_depth(d.id)
        return correct, aod, rr, anc, depth

    def holdout_accuracy(self) -> float:
        """
        Conventional monitor: fixed clean eval on FRESH entities with no
        accumulated state. This is what an operator's dashboard sees.
        """
        n = self.cfg["holdout_size"]
        hits = 0
        for _ in range(n):
            self.holdout_id += 1
            e = f"h{self.holdout_id:06d}"
            self.truth[e] = self.rng.randint(0, 1)
            obs = self._observe(e, self.cfg["ai_noise"])
            hits += int(obs == self.truth[e])
        return hits / n

    # -- main loop --------------------------------------------------------

    def run(self) -> List[dict]:
        cfg = self.cfg
        rows = []
        entities = list(self.truth.keys())
        for cycle in range(1, cfg["cycles"] + 1):
            batch = self.rng.sample(entities, cfg["batch_size"])
            for e in batch:
                for _ in range(cfg["writes_per_entity"]):
                    self.producer_write(e, cycle)

            correct = aods = rrs = ancs = depths = 0.0
            for e in batch:
                c, aod, rr, anc, depth = self.decide(e, cycle)
                correct += c
                aods += aod
                rrs += rr
                ancs += anc
                depths += depth
            n = len(batch)
            rows.append({
                "cycle": cycle,
                "live_quality": correct / n,          # hidden from operator
                "holdout_accuracy": self.holdout_accuracy(),  # operator sees this
                "AOD": aods / n,
                "RR": rrs / n,
                "ancestry_size": ancs / n,
                "propagation_depth": depths / n,
            })
        return rows


# --------------------------------------------------------------------------

# Entity pool deliberately smaller than batch*cycles so that entities are
# revisited many times and state actually accumulates. With n=100, batch=40,
# cycles=30 each entity is touched ~12 times.
BASE = {
    "n_entities": 100, "cycles": 30, "batch_size": 40,
    "writes_per_entity": 1, "holdout_size": 2000,
    "ai_noise": 0.25, "human_noise": 0.10,
    "confirmation_weight": 0.7,
    "laundering_rate": 0.0,
}

ARMS = {
    # A1: human-clean control — no AI-origin state, no feedback
    "A1": {**BASE, "ai_write_fraction": 0.0, "feedback": False},
    # A3: treatment — AI-origin state WITH feedback loop
    "A3": {**BASE, "ai_write_fraction": 1.0, "feedback": True},
    # A9: matched-write-volume control — AI-origin state, NO feedback.
    #     Mandatory: rules out "degradation came from more writes".
    "A9": {**BASE, "ai_write_fraction": 1.0, "feedback": False},
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arms", default="A1,A3,A9")
    p.add_argument("--seeds", default="1,2,3,4,5")
    p.add_argument("--out", default="results/raw")
    args = p.parse_args()

    os.makedirs(args.out, exist_ok=True)
    all_rows = []
    for arm in args.arms.split(","):
        cfg = ARMS[arm]
        chash = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]
        for seed in [int(s) for s in args.seeds.split(",")]:
            rows = Sim(cfg, seed).run()
            for r in rows:
                r.update({"arm": arm, "seed": seed, "config_hash": chash})
            all_rows.extend(rows)
            with open(f"{args.out}/{arm}_seed{seed}.json", "w") as f:
                json.dump({"arm": arm, "seed": seed, "config": cfg,
                           "config_hash": chash, "rows": rows}, f, indent=2)
    with open(f"{args.out}/all_rows.json", "w") as f:
        json.dump(all_rows, f)
    print(f"wrote {len(all_rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
