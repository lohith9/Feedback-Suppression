#!/usr/bin/env python3
"""Reproduce published C1/C2 reference results through the NEW architecture.
$0, CPU-only, deterministic. Does NOT overwrite immutable raw results; it
regenerates and verifies bit-exact equality against them.
Usage:
  python reproduce.py --scenario synthetic --experiment c1
  python reproduce.py --scenario synthetic --experiment c2
"""
import argparse, json, os, sys
ROOT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ROOT)
from src.experiments.controller import run_c1_condition, run_c2_condition, C1_CONDITIONS, C1_REGIMES

def _verify(new, pub, keys=("cycle","quality","AOD","RR","writes","observations","cum_regret")):
    return len(new)==len(pub) and all(x[k]==y[k] for x,y in zip(new,pub) for k in keys)

def c1():
    raw = json.load(open(os.path.join(ROOT,"pilot/phase1b/results/raw/stage1_corrected_run_20260816_002729_n30/stage1_corrected.json")))
    idx = {(r["truth_mode"],r["writeback"],r["deference_weight"],r["seed"]):r for r in raw}
    ok=tot=0
    for tm in C1_REGIMES:
        for wb,w in C1_CONDITIONS:
            for s in range(1,31):
                tot+=1; ok+= _verify(run_c1_condition(tm,w,wb,s), idx[(tm,wb,w,s)]["rows"])
    print(f"C1 via new architecture: {ok}/{tot} runs reproduce published raw EXACTLY")
    return ok==tot

def c2():
    raw = json.load(open(os.path.join(ROOT,"pilot/phase1b/results/raw/c2_correlated_run_20260816_125534/c2_correlated.json")))
    idx = {(r["rho"],r["condition"],r["seed"]):r for r in raw}
    conds={"reference":(False,0.0),"behavioural":(False,0.7),"architectural":(True,0.0)}
    ok=tot=0
    for rho in [0.0,0.3,0.6,0.9]:
        for name,(wb,w) in conds.items():
            for s in range(1,31):
                tot+=1; ok+= _verify(run_c2_condition(name,w,wb,rho,s), idx[(rho,name,s)]["rows"])
    print(f"C2 via new architecture: {ok}/{tot} runs reproduce published raw EXACTLY")
    return ok==tot

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--scenario",default="synthetic"); ap.add_argument("--experiment",choices=["c1","c2"],required=True)
    a=ap.parse_args()
    assert a.scenario=="synthetic", "only the synthetic reference scenario exists in this migration"
    ok = c1() if a.experiment=="c1" else c2()
    sys.exit(0 if ok else 1)
