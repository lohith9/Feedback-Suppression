import json,sys,statistics as st,math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
RUN=sys.argv[1]; OUT="results/figures/c2"
recs=json.load(open(f"{RUN}/c2_correlated.json"))
idx={(r["rho"],r["condition"],r["seed"]):r for r in recs}
RHOS=sorted({r["rho"] for r in recs}); SEEDS=sorted({r["seed"] for r in recs})
CONDS=[("reference","#27ae60"),("behavioural","#e67e22"),("architectural","#8e44ad")]
C=range(1,41)
def q(r,c): return [x["quality"] for x in r["rows"] if x["cycle"]==c][0]
def tr(rho,cond): return [st.mean([q(idx[(rho,cond,s)],c) for s in SEEDS]) for c in C]
def bnd(rho,cond):
    lo=[];hi=[]
    for c in C:
        v=[q(idx[(rho,cond,s)],c) for s in SEEDS]; m,sd=st.mean(v),st.pstdev(v)
        lo.append(m-sd);hi.append(m+sd)
    return lo,hi

# C2.1 trajectories per rho
f,ax=plt.subplots(1,4,figsize=(18,4.2),sharey=True)
for i,rho in enumerate(RHOS):
    for cond,col in CONDS:
        ax[i].plot(C,tr(rho,cond),lw=2,color=col,label=cond)
        lo,hi=bnd(rho,cond); ax[i].fill_between(C,lo,hi,color=col,alpha=.13)
    ax[i].axvline(15,ls="--",c="k",lw=1); ax[i].axhline(0.70,ls=":",c="gray")
    ax[i].set_title(f"rho = {rho}"); ax[i].set_xlabel("cycle"); ax[i].grid(alpha=.3)
ax[0].set_ylabel("decision quality"); ax[0].legend(fontsize=8); ax[0].set_ylim(0.1,1.0)
f.suptitle("Fig C2.1 — Adaptation trajectories by correlation level (30 seeds, ±1 sd)",y=1.02)
f.tight_layout(); f.savefig(f"{OUT}/figC2_1_trajectories.png",dpi=140,bbox_inches="tight"); plt.close(f)

# C2.2 gap vs rho  + C2.3 effect size vs rho
gaps={}; effs={}
for rho in RHOS:
    for cond,_ in CONDS[1:]:
        d=[q(idx[(rho,'reference',s)],40)-q(idx[(rho,cond,s)],40) for s in SEEDS]
        m=st.mean(d); sd=st.stdev(d); h=1.96*sd/math.sqrt(len(d))
        gaps[(rho,cond)]=(m,h); effs[(rho,cond)]=m/sd
f,ax=plt.subplots(1,2,figsize=(12.5,4.4))
for cond,col in CONDS[1:]:
    y=[gaps[(r,cond)][0] for r in RHOS]; e=[gaps[(r,cond)][1] for r in RHOS]
    ax[0].errorbar(RHOS,y,yerr=e,fmt="o-",lw=2,color=col,capsize=4,label=cond)
    ax[1].plot(RHOS,[effs[(r,cond)] for r in RHOS],"o-",lw=2,color=col,label=cond)
ax[0].axhline(0.10,ls=":",c="r"); ax[0].text(0.01,0.115,"practical floor 0.10",fontsize=7,color="r")
ax[0].set_ylim(0,0.65); ax[0].set_xlabel("correlation rho"); ax[0].set_ylabel("adaptation gap @ +25 (95% CI)")
ax[0].set_title("Fig C2.2 — Gap vs correlation"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
ax[1].set_xlabel("correlation rho"); ax[1].set_ylabel("paired Cohen's d")
ax[1].set_title("Fig C2.3 — Effect size vs correlation"); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
f.tight_layout(); f.savefig(f"{OUT}/figC2_2_3_gap_effect.png",dpi=140); plt.close(f)

# C2.4 reference vs feedback, seed-level
f,ax=plt.subplots(figsize=(8.6,4.6))
x=range(len(RHOS)); wd=0.26
for j,(cond,col) in enumerate(CONDS):
    for i,rho in enumerate(RHOS):
        v=[q(idx[(rho,cond,s)],40) for s in SEEDS]
        ax.scatter([i+(j-1)*wd]*len(v),v,s=9,color=col,alpha=.45,zorder=2)
        ax.scatter([i+(j-1)*wd],[st.mean(v)],s=90,color=col,edgecolor="k",zorder=3,
                   label=cond if i==0 else "")
ax.set_xticks(list(x)); ax.set_xticklabels([f"rho={r}" for r in RHOS])
ax.set_ylabel("quality @ c40"); ax.axhline(0.70,ls=":",c="gray")
ax.set_title("Fig C2.4 — Reference vs feedback across correlation (individual seeds shown)")
ax.legend(fontsize=8); ax.grid(alpha=.3,axis="y")
f.tight_layout(); f.savefig(f"{OUT}/figC2_4_seedlevel.png",dpi=140); plt.close(f)
print("4 C2 figures ->",OUT)
