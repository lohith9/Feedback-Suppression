import json, sys, statistics as st, math
from collections import defaultdict
RUN = sys.argv[1]
Q, PERSIST, CH = 0.70, 3, 15
WINDOWS = [0, 3, 5, 10, 25]
recs = json.load(open(f"{RUN}/stage1_corrected.json"))
idx = {(r["truth_mode"], r["writeback"], r["deference_weight"], r["seed"]): r for r in recs}
SEEDS = sorted({r["seed"] for r in recs})
CONDS = [(False,0.0),(False,0.3),(False,0.7),(False,0.9),(True,0.0),(True,0.7),(True,0.9)]

def q(r,c): return [x["quality"] for x in r["rows"] if x["cycle"]==c][0]
def adapt(r):
    post=[x for x in r["rows"] if x["cycle"]>=CH]
    for i in range(len(post)-PERSIST+1):
        if all(post[i+k]["quality"]>=Q for k in range(PERSIST)): return post[i]["cycle"]-CH
    return None
def ci95(v):
    if len(v)<2: return (0,0)
    m,s=st.mean(v),st.stdev(v); h=1.96*s/math.sqrt(len(v)); return (m-h,m+h)
def nm(wb,w): return f"wb={'ON ' if wb else 'OFF'} w={w}"

print("="*104); print("CORRECTED STAGE 1 — 7 conditions x 2 regimes x 10 seeds (frozen prereg, thr=0.70/3)"); print("="*104)

print("\nTABLE 1 — Quality by condition and regime  (mean [95% CI])")
print(f"{'condition':<16}{'regime':<14}{'c14 pre':>16}{'c16 post':>16}{'c25 (+10)':>16}{'c40 (+25)':>16}{'cum regret':>12}")
T1={}
for wb,w in CONDS:
    for tm in ["static","abrupt_shift"]:
        rs=[idx[(tm,wb,w,s)] for s in SEEDS]
        cells=[]
        for c in [14,16,25,40]:
            v=[q(r,c) for r in rs]; lo,hi=ci95(v); cells.append(f"{st.mean(v):.3f}[{lo:.2f},{hi:.2f}]")
        reg=st.mean([r["rows"][-1]["cum_regret"] for r in rs])
        T1[(wb,w,tm)]={"c14":st.mean([q(r,14) for r in rs]),"c16":st.mean([q(r,16) for r in rs]),
                       "c25":st.mean([q(r,25) for r in rs]),"c40":st.mean([q(r,40) for r in rs]),"regret":reg}
        print(f"{nm(wb,w):<16}{tm:<14}"+"".join(f"{c:>16}" for c in cells)+f"{reg:>12.0f}")

print("\nTABLE 2 — Adaptation time after truth change (cycles to reach >=0.70 sustained 3; C=censored)")
print(f"{'condition':<16}{'adapted':>9}{'median':>9}   per-seed")
T2={}
for wb,w in CONDS:
    ts=[adapt(idx[("abrupt_shift",wb,w,s)]) for s in SEEDS]
    ok=[t for t in ts if t is not None]; T2[(wb,w)]=(len(ok),st.median(ok) if ok else None)
    print(f"{nm(wb,w):<16}{len(ok):>6}/{len(SEEDS)}{(st.median(ok) if ok else 'CENSORED'):>9}   "
          +",".join('C' if t is None else str(t) for t in ts))

print("\nTABLE 3 — Adaptation gap vs reference (wb=OFF,w=0.0), PAIRED by seed, abrupt shift")
print(f"{'condition':<16}{'window':>8}{'gap':>9}{'sd':>8}{'95% CI':>18}{'d':>8}{'sameDir':>9}")
GAP={}
for wb,w in CONDS[1:]:
    for win in WINDOWS:
        c=CH+win
        d=[q(idx[("abrupt_shift",False,0.0,s)],c)-q(idx[("abrupt_shift",wb,w,s)],c) for s in SEEDS]
        m,sd=st.mean(d),st.pstdev(d); lo,hi=ci95(d)
        eff=m/st.stdev(d) if len(d)>1 and st.stdev(d)>1e-9 else float('inf')
        GAP[(wb,w,win)]=m
        print(f"{nm(wb,w):<16}{win:>8}{m:>9.3f}{sd:>8.3f}{f'[{lo:.3f},{hi:.3f}]':>18}{eff:>8.2f}"
              f"{sum(1 for x in d if x>0)/len(d):>9.0%}")

print("\nTABLE 4 — STATIC CONTROL: same gap computed under static truth (mandatory comparator)")
print(f"{'condition':<16}{'static gap c40':>16}{'abrupt gap c40':>16}{'difference':>13}")
for wb,w in CONDS[1:]:
    ds=[q(idx[("static",False,0.0,s)],40)-q(idx[("static",wb,w,s)],40) for s in SEEDS]
    da=[q(idx[("abrupt_shift",False,0.0,s)],40)-q(idx[("abrupt_shift",wb,w,s)],40) for s in SEEDS]
    print(f"{nm(wb,w):<16}{st.mean(ds):>16.3f}{st.mean(da):>16.3f}{st.mean(da)-st.mean(ds):>13.3f}")

print("\nTABLE 5 — Factor analysis")
print("  Factor A (deference), write-back OFF, abrupt c40:")
for w in [0.0,0.3,0.7,0.9]:
    print(f"    w={w}: {T1[(False,w,'abrupt_shift')]['c40']:.3f}")
print("  Factor B (write-back) at matched w, abrupt c40:")
for w in [0.0,0.7,0.9]:
    print(f"    w={w}: OFF={T1[(False,w,'abrupt_shift')]['c40']:.3f}  ON={T1[(True,w,'abrupt_shift')]['c40']:.3f}"
          f"  ΔB={T1[(True,w,'abrupt_shift')]['c40']-T1[(False,w,'abrupt_shift')]['c40']:+.3f}")
print("  Interaction A x B (does B's effect depend on w?):")
b0=T1[(True,0.0,'abrupt_shift')]['c40']-T1[(False,0.0,'abrupt_shift')]['c40']
b9=T1[(True,0.9,'abrupt_shift')]['c40']-T1[(False,0.9,'abrupt_shift')]['c40']
print(f"    ΔB at w=0.0: {b0:+.3f}   ΔB at w=0.9: {b9:+.3f}   interaction: {b9-b0:+.3f}")

print("\nTABLE 6 — Provenance signals (abrupt, c40) — do they track HARM or only CONFIGURATION?")
print(f"{'condition':<16}{'AOD':>8}{'RR':>8}{'writes':>9}{'obs':>8}{'adapted?':>10}")
for wb,w in CONDS:
    rs=[idx[("abrupt_shift",wb,w,s)] for s in SEEDS]
    last=[r["rows"][-1] for r in rs]
    print(f"{nm(wb,w):<16}{st.mean([x['AOD'] for x in last]):>8.3f}{st.mean([x['RR'] for x in last]):>8.3f}"
          f"{last[0]['writes']:>9}{last[0]['observations']:>8}{('YES' if T2[(wb,w)][0]>5 else 'NO'):>10}")

json.dump({"T1":{f"{k[0]}|{k[1]}|{k[2]}":v for k,v in T1.items()},
           "T2":{f"{k[0]}|{k[1]}":v for k,v in T2.items()},
           "GAP":{f"{k[0]}|{k[1]}|{k[2]}":v for k,v in GAP.items()}},
          open(f"{RUN}/analysis_summary.json","w"),indent=2)
print(f"\nwrote {RUN}/analysis_summary.json")
