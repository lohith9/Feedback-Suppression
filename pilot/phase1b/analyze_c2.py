import json,sys,statistics as st,math
RUN=sys.argv[1]
Q,PERSIST,CH=0.70,3,15; WIN=[0,3,5,10,25]; FLOOR=0.10
recs=json.load(open(f"{RUN}/c2_correlated.json"))
idx={(r["rho"],r["condition"],r["seed"]):r for r in recs}
RHOS=sorted({r["rho"] for r in recs}); SEEDS=sorted({r["seed"] for r in recs})
CONDS=["reference","behavioural","architectural"]
def q(r,c): return [x["quality"] for x in r["rows"] if x["cycle"]==c][0]
def adapt(r):
    post=[x for x in r["rows"] if x["cycle"]>=CH]
    for i in range(len(post)-PERSIST+1):
        if all(post[i+k]["quality"]>=Q for k in range(PERSIST)): return post[i]["cycle"]-CH
    return None
def ci(v):
    m=st.mean(v); s=st.stdev(v) if len(v)>1 else 0; h=1.96*s/math.sqrt(len(v)); return m,(m-h,m+h),s

print("="*100); print("C2 — CORRELATED NOISE (persistent entity bias), 3 conditions x 4 rho x 30 seeds")
print("="*100)

print("\nTABLE C2.1 — Post-shift quality (mean [95% CI]) and adaptation rate")
print(f"{'rho':>5}{'condition':>16}{'q@c25 (+10)':>22}{'q@c40 (+25)':>22}{'adapted':>10}")
for rho in RHOS:
    for c in CONDS:
        rs=[idx[(rho,c,s)] for s in SEEDS]
        m25,ci25,_=ci([q(r,25) for r in rs]); m40,ci40,_=ci([q(r,40) for r in rs])
        ad=sum(1 for r in rs if adapt(r) is not None)
        print(f"{rho:>5}{c:>16}{f'{m25:.3f}[{ci25[0]:.2f},{ci25[1]:.2f}]':>22}"
              f"{f'{m40:.3f}[{ci40[0]:.2f},{ci40[1]:.2f}]':>22}{f'{ad}/30':>10}")

print("\nTABLE C2.2 — Adaptation gap vs reference (paired by seed) @ +25 cycles")
print(f"{'rho':>5}{'condition':>16}{'gap':>9}{'sd':>8}{'95% CI':>20}{'d':>8}{'sameDir':>9}{'verdict':>14}")
GAPS={}
for rho in RHOS:
    for c in CONDS[1:]:
        d=[q(idx[(rho,'reference',s)],40)-q(idx[(rho,c,s)],40) for s in SEEDS]
        m,cc,sd=ci(d); eff=m/sd if sd>1e-9 else float('inf')
        GAPS[(rho,c)]=(m,cc,eff)
        v="SURVIVES" if (m>=FLOOR and cc[0]>0) else ("BELOW FLOOR" if cc[0]>0 else "CI includes 0")
        print(f"{rho:>5}{c:>16}{m:>9.3f}{sd:>8.3f}{f'[{cc[0]:.3f},{cc[1]:.3f}]':>20}{eff:>8.2f}"
              f"{sum(1 for x in d if x>0)/len(d):>9.0%}{v:>14}")

print("\nTABLE C2.3 — Attenuation across rho (gap @ +25)")
print(f"{'condition':>16}"+"".join(f"{'rho='+str(r):>12}" for r in RHOS)+f"{'% retained':>12}")
for c in CONDS[1:]:
    g=[GAPS[(r,c)][0] for r in RHOS]
    print(f"{c:>16}"+"".join(f"{x:>12.3f}" for x in g)+f"{g[-1]/g[0]*100:>11.0f}%")

print("\nTABLE C2.4 — Reference-condition recovery (the mechanism under test)")
print(f"{'rho':>5}{'ref q@c40':>12}{'ref adapted':>14}{'interpretation':>40}")
for rho in RHOS:
    rs=[idx[(rho,'reference',s)] for s in SEEDS]
    m,_,_=ci([q(r,40) for r in rs]); ad=sum(1 for r in rs if adapt(r) is not None)
    note=("recovers via independent evidence" if ad>15 else
          "recovery weakened" if ad>3 else "recovery largely lost")
    print(f"{rho:>5}{m:>12.3f}{f'{ad}/30':>14}{note:>40}")

print("\nREGRESSION CHECK — rho=0.0 must match C1 (independent noise)")
c1=json.load(open("results/raw/stage1_corrected_run_20260816_002729_n30/stage1_corrected.json"))
c1i={(x["writeback"],x["deference_weight"],x["seed"]):x for x in c1 if x["truth_mode"]=="abrupt_shift"}
for c,wb,w in [("reference",False,0.0),("behavioural",False,0.7),("architectural",True,0.0)]:
    a=st.mean([q(idx[(0.0,c,s)],40) for s in SEEDS]); b=st.mean([q(c1i[(wb,w,s)],40) for s in SEEDS])
    print(f"  {c:<15} C2(rho=0)={a:.3f}  C1={b:.3f}  diff={abs(a-b):.3f} {'OK' if abs(a-b)<0.03 else 'MISMATCH'}")

json.dump({f"{k[0]}|{k[1]}":{"gap":v[0],"ci":v[1],"d":v[2]} for k,v in GAPS.items()},
          open(f"{RUN}/c2_analysis.json","w"),indent=2)
print(f"\nwrote {RUN}/c2_analysis.json")
