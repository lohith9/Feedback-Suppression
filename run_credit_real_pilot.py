"""REAL UCI credit-risk 5-seed pilot. $0, CPU-only, deterministic.
Reuses the frozen Sim1C mechanism via run_credit_condition. Emits results CSV."""
import sys, csv, statistics as st
sys.path.insert(0,'.')
from src.scenarios.credit_risk import CreditRiskScenario
from src.experiments.controller import run_credit_condition
from src.evaluation.adaptation import adaptation_time, quality_at

SEEDS=[1,2,3,4,5]; CH=15; SHOCK=2.0; N=100
CONDS=[("reference",False,0.0),("behavioural",False,0.7),("architectural",True,0.0)]
REGIMES=["static","abrupt_shift"]

def scen(tm,seed): return CreditRiskScenario(n_entities=N,mode=tm,change_cycle=CH,shock=SHOCK,seed=seed).load()

rows=[]
qfinal={}  # (regime,condition,seed)->quality_final for paired gap
# first pass: run everything, cache
runs={}
for tm in REGIMES:
    for name,wb,w in CONDS:
        for s in SEEDS:
            sc=scen(tm,s); sc.initialize_truth(); d=sc.describe()
            r=run_credit_condition(sc,w,wb,s)
            runs[(tm,name,s)]=(r,d)
            qfinal[(tm,name,s)]=quality_at(r,40)
# second pass: metrics + paired gap vs reference
for tm in REGIMES:
    for name,wb,w in CONDS:
        for s in SEEDS:
            r,d=runs[(tm,name,s)]
            at=adaptation_time(r,CH,0.70,3)
            gap=qfinal[(tm,"reference",s)]-qfinal[(tm,name,s)]
            last=r[-1]
            rows.append({
                "scenario":"credit_risk_UCI350","truth_regime":tm,"condition":name,"seed":s,
                "baseline_prevalence":d["baseline_prevalence"],"post_shift_prevalence":d["post_prevalence"],
                "flip_fraction":d["flip_fraction"],
                "quality_start":round(quality_at(r,1),4),
                "quality_post_shift":round(quality_at(r,CH+1),4),
                "quality_final":round(quality_at(r,40),4),
                "adaptation_time":("" if at is None else at),
                "adapted":(1 if at is not None else 0),
                "adaptation_gap":round(gap,4),
                "writes":last["writes"],"observations":last["observations"],
                "AOD":round(last["AOD"],4),"RR":round(last["RR"],4)})
cols=["scenario","truth_regime","condition","seed","baseline_prevalence","post_shift_prevalence",
      "flip_fraction","quality_start","quality_post_shift","quality_final","adaptation_time",
      "adapted","adaptation_gap","writes","observations","AOD","RR"]
with open("CREDIT_RISK_REAL_PILOT_RESULTS.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); [w.writerow(x) for x in rows]
print("wrote CREDIT_RISK_REAL_PILOT_RESULTS.csv:",len(rows),"rows")

# summary
print("\nmeasured flip fraction (abrupt, per seed):",
      [runs[('abrupt_shift','reference',s)][1]['flip_fraction'] for s in SEEDS])
print("\n== SUMMARY (mean over 5 seeds) ==")
print(f"{'regime':<13}{'condition':<14}{'q_start':>8}{'q_post':>8}{'q_final':>9}{'adapted':>9}{'gap@40':>8}")
for tm in REGIMES:
    for name,_,_ in CONDS:
        rs=[x for x in rows if x['truth_regime']==tm and x['condition']==name]
        print(f"{tm:<13}{name:<14}"
              f"{st.mean(x['quality_start'] for x in rs):>8.3f}"
              f"{st.mean(x['quality_post_shift'] for x in rs):>8.3f}"
              f"{st.mean(x['quality_final'] for x in rs):>9.3f}"
              f"{sum(x['adapted'] for x in rs):>6}/5"
              f"{st.mean(x['adaptation_gap'] for x in rs):>8.3f}")
# write-volume invariant check
print("\nwrite-volume (abrupt, seed1):", {name:runs[('abrupt_shift',name,1)][0][-1]['writes'] for name,_,_ in CONDS})
