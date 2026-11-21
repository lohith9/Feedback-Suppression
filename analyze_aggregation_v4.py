#!/usr/bin/env python3
"""Locked analysis for V4 (preregistration/AGGREGATION_ABLATION_V4.yaml). Usage:
  python analyze_aggregation_v4.py results/raw/aggregation_v4_<stamp>
"""
import sys, os, json, math, statistics as st
RUN = sys.argv[1]
recs = json.load(open(os.path.join(RUN, "aggregation_v4.json")))
AGGS = ["CUM", "WIN5", "WIN10", "LWW", "EXP"]; CH, Q, P, FLOOR = 15, 0.70, 3, 0.10
idx = {(r["aggregator"], r["regime"], r["condition"], r["seed"]): r for r in recs}
SEEDS = sorted({r["seed"] for r in recs})

def q40(r): return [x["quality"] for x in r["rows"] if x["cycle"] == 40][0]
def ci(v):
    m, s = st.mean(v), st.stdev(v); h = 1.96 * s / math.sqrt(len(v)); return m, m - h, m + h, (m / s if s > 1e-12 else float("inf"))
def gap(a, reg, c, s): return q40(idx[(a, reg, "REF", s)]) - q40(idx[(a, reg, c, s)])
def dadapt(a, c, s): return gap(a, "abrupt_shift", c, s) - gap(a, "static", c, s)
def adapt(r):
    post = [x for x in r["rows"] if x["cycle"] >= CH]
    for i in range(len(post) - P + 1):
        if all(post[i + k]["quality"] >= Q for k in range(P)): return post[i]["cycle"] - CH
    return None
def verdict(m, lo, hi):
    if lo > 0 and m >= FLOOR: return "PRESENT"
    if hi < FLOOR: return "ABSENT"
    return "INCONCLUSIVE"

out = {"aggregators": {}}
for a in AGGS:
    res = {}
    for c in ["A", "B", "AB"]:
        v = [dadapt(a, c, s) for s in SEEDS]; m, lo, hi, d = ci(v)
        res[c] = {"Delta_adapt": m, "ci": [lo, hi], "d": d, "same_dir": sum(x > 0 for x in v) / len(v), "verdict": verdict(m, lo, hi)}
    qa = {c: st.mean(q40(idx[(a, "abrupt_shift", c, s)]) for s in SEEDS) for c in ["REF", "A", "B", "AB"]}
    qs = {c: st.mean(q40(idx[(a, "static", c, s)]) for s in SEEDS) for c in ["REF", "A", "B", "AB"]}
    ident = (qa["A"] - qa["AB"] >= 0.05) and (qa["B"] - qa["AB"] >= 0.05)
    iv = [dadapt(a, "AB", s) - dadapt(a, "A", s) - dadapt(a, "B", s) for s in SEEDS]; m, lo, hi, d = ci(iv)
    add = ("ADDITIVE" if lo <= 0 <= hi else "SUB_ADDITIVE" if hi < 0 else "SUPER_ADDITIVE") if ident else "SATURATED (not interpreted)"
    adapted = {c: sum(adapt(idx[(a, "abrupt_shift", c, s)]) is not None for s in SEEDS) for c in ["REF", "A", "B", "AB"]}
    res["q40_abrupt"] = qa; res["q40_static"] = qs
    res["interaction"] = {"mean": m, "ci": [lo, hi], "identifiable": ident, "verdict": add}
    res["adapted_of_30"] = adapted
    out["aggregators"][a] = res

json.dump(out, open(os.path.join(RUN, "analysis_v4.json"), "w"), indent=2)
print(f"{'agg':6} {'cond':4} {'Delta_adapt':>11} {'95% CI':>18} {'d':>6} {'same':>5}  verdict")
for a in AGGS:
    for c in ["A", "B", "AB"]:
        r = out["aggregators"][a][c]
        print(f"{a:6} {c:4} {r['Delta_adapt']:11.3f} [{r['ci'][0]:+.3f},{r['ci'][1]:+.3f}] {r['d']:6.2f} {r['same_dir']:5.0%}  {r['verdict']}")
    I = out["aggregators"][a]["interaction"]
    print(f"{a:6} AxB  {I['mean']:11.3f} [{I['ci'][0]:+.3f},{I['ci'][1]:+.3f}]  {I['verdict']}")
    print(f"{'':6} q40 abrupt {json.dumps({k: round(v,3) for k,v in out['aggregators'][a]['q40_abrupt'].items()})}  static {json.dumps({k: round(v,3) for k,v in out['aggregators'][a]['q40_static'].items()})}  adapted {out['aggregators'][a]['adapted_of_30']}")
