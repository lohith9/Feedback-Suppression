#!/usr/bin/env python3
"""V4 aggregation ablation runner. Usage:
  python run_aggregation_v4.py check-i1      # invariant I1 vs published C1 raw
  python run_aggregation_v4.py smoke         # seeds 1..3, invariants I2/I3 only
  python run_aggregation_v4.py confirmatory  # seeds 101..130, writes raw results
"""
import sys, os, json, hashlib, datetime
ROOT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ROOT)
from src.experiments.aggregation_controller import run_agg_condition, AGGREGATORS, CONDITIONS, CODE_VERSION

PREREG = os.path.join(ROOT, "preregistration/AGGREGATION_ABLATION_V4.yaml")
EXPECTED_SHA = open(os.path.join(ROOT, "preregistration/AGGREGATION_ABLATION_V4.sha256")).read().split("sha256:")[1].split()[0]
KEYS = ("cycle", "quality", "AOD", "RR", "writes", "observations", "cum_regret")

def prereg_ok():
    h = hashlib.sha256(open(PREREG, "rb").read()).hexdigest()
    assert h == EXPECTED_SHA, f"PREREGISTRATION CHANGED: {h}"
    return h

def check_i1():
    raw = json.load(open(os.path.join(ROOT, "pilot/phase1b/results/raw/stage1_corrected_run_20260816_002729_n30/stage1_corrected.json")))
    idx = {(r["truth_mode"], r["writeback"], r["deference_weight"], r["seed"]): r for r in raw}
    ok = tot = 0
    for reg in ["static", "abrupt_shift"]:
        for name, (wb, w) in CONDITIONS.items():
            key = (reg, wb, w)
            if (reg, wb, w, 1) not in idx:
                continue
            for s in range(1, 31):
                tot += 1
                new = run_agg_condition("CUM", reg, wb, w, s)
                pub = idx[(reg, wb, w, s)]["rows"]
                ok += len(new) == len(pub) and all(x[k] == y[k] for x, y in zip(new, pub) for k in KEYS)
    print(f"I1: CUM reproduces published C1 raw EXACTLY in {ok}/{tot} runs")
    return ok == tot and tot > 0

def run(seeds, inspect_estimands):
    recs = []
    for agg in AGGREGATORS:
        for reg in ["static", "abrupt_shift"]:
            for s in seeds:
                writes = {}
                for name, (wb, w) in CONDITIONS.items():
                    rows = run_agg_condition(agg, reg, wb, w, s)
                    writes[name] = rows[-1]["writes"]
                    recs.append({"aggregator": agg, "regime": reg, "condition": name,
                                 "writeback": wb, "w": w, "seed": s, "rows": rows})
                # I2 write-volume invariant
                assert writes["REF"] == writes["B"] and writes["A"] == writes["AB"], f"I2 FAIL {agg} {reg} {s} {writes}"
    # I3 paired design: observation counts identical across conditions for a seed
    obs = {}
    for r in recs:
        obs.setdefault((r["aggregator"], r["regime"], r["seed"]), set()).add(r["rows"][-1]["observations"])
    assert all(len(v) == 1 for v in obs.values()), "I3 FAIL"
    return recs

if __name__ == "__main__":
    mode = sys.argv[1]
    sha = prereg_ok()
    if mode == "check-i1":
        sys.exit(0 if check_i1() else 1)
    if mode == "smoke":
        recs = run([1, 2, 3], False)
        print(f"SMOKE: {len(recs)} runs, invariants I2/I3 PASS (no estimands inspected)")
        sys.exit(0)
    if mode == "confirmatory":
        assert check_i1(), "I1 FAILED - INVALID"
        recs = run(list(range(101, 131)), True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out = os.path.join(ROOT, f"results/raw/aggregation_v4_{stamp}")
        os.makedirs(out)
        json.dump(recs, open(os.path.join(out, "aggregation_v4.json"), "w"))
        json.dump({"code_version": CODE_VERSION, "prereg_sha256": sha, "runs": len(recs),
                   "seeds": "101..130", "timestamp": stamp}, open(os.path.join(out, "manifest.json"), "w"), indent=2)
        print(f"CONFIRMATORY: {len(recs)} runs written to {out}")
