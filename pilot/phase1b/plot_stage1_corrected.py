import json,sys,statistics as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
RUN=sys.argv[1]; OUT="results/figures/stage1_corrected"
recs=json.load(open(f"{RUN}/stage1_corrected.json"))
idx={(r["truth_mode"],r["writeback"],r["deference_weight"],r["seed"]):r for r in recs}
SEEDS=sorted({r["seed"] for r in recs}); C=list(range(1,41)); CH=15; Q=0.70
def tr(tm,wb,w):
    rs=[idx[(tm,wb,w,s)] for s in SEEDS]
    return [st.mean([r["rows"][c-1]["quality"] for r in rs]) for c in C]
def band(tm,wb,w):
    rs=[idx[(tm,wb,w,s)] for s in SEEDS]
    lo=[];hi=[]
    for c in C:
        v=[r["rows"][c-1]["quality"] for r in rs]; m,s_=st.mean(v),st.pstdev(v); lo.append(m-s_);hi.append(m+s_)
    return lo,hi
def adapt(r):
    post=[x for x in r["rows"] if x["cycle"]>=CH]
    for i in range(len(post)-2):
        if all(post[i+k]["quality"]>=Q for k in range(3)): return post[i]["cycle"]-CH
    return None

# F1 static vs abrupt
f,a=plt.subplots(figsize=(6.4,4.2))
for tm,c,l in [("static","#27ae60","static truth"),("abrupt_shift","#c0392b","abrupt shift @c15")]:
    a.plot(C,tr(tm,False,0.0),lw=2,color=c,label=l); lo,hi=band(tm,False,0.0); a.fill_between(C,lo,hi,color=c,alpha=.15)
a.axvline(CH,ls="--",c="k",lw=1); a.set_xlabel("cycle"); a.set_ylabel("decision quality")
a.set_title("Fig 1 — Truth regimes (reference condition wb=OFF, w=0.0)"); a.legend(); a.grid(alpha=.3)
f.tight_layout(); f.savefig(f"{OUT}/fig1_truth_regimes.png",dpi=140); plt.close(f)

# F2 wb OFF across w  /  F3 wb ON across w
for fign,wb,tag in [(2,False,"OFF"),(3,True,"ON")]:
    ws=[0.0,0.3,0.7,0.9] if not wb else [0.0,0.7,0.9]
    f,a=plt.subplots(figsize=(6.4,4.2))
    for w,c in zip(ws,["#27ae60","#f39c12","#e67e22","#c0392b"]):
        a.plot(C,tr("abrupt_shift",wb,w),lw=2,color=c,label=f"w={w}")
        lo,hi=band("abrupt_shift",wb,w); a.fill_between(C,lo,hi,color=c,alpha=.12)
    a.axvline(CH,ls="--",c="k",lw=1); a.axhline(Q,ls=":",c="gray")
    a.text(1,Q+.01,"pre-registered 0.70",fontsize=7,color="gray")
    a.set_xlabel("cycle"); a.set_ylabel("decision quality"); a.set_ylim(0.1,1.02)
    a.set_title(f"Fig {fign} — Adaptation, write-back {tag}"); a.legend(fontsize=8); a.grid(alpha=.3)
    f.tight_layout(); f.savefig(f"{OUT}/fig{fign}_writeback_{tag.lower()}.png",dpi=140); plt.close(f)

# F4 quality vs w
f,a=plt.subplots(figsize=(6.4,4.2))
for wb,c,l,ws in [(False,"#c0392b","write-back OFF",[0.0,0.3,0.7,0.9]),(True,"#8e44ad","write-back ON",[0.0,0.7,0.9])]:
    y=[tr("abrupt_shift",wb,w)[39] for w in ws]
    ysd=[st.pstdev([idx[("abrupt_shift",wb,w,s)]["rows"][39]["quality"] for s in SEEDS]) for w in ws]
    a.errorbar(ws,y,yerr=ysd,fmt="o-",lw=2,color=c,label=l,capsize=3)
a.set_xlabel("producer deference weight w"); a.set_ylabel("quality @ c40 (+25)")
a.set_title("Fig 4 — Post-shift quality vs deference weight"); a.legend(fontsize=8); a.grid(alpha=.3)
f.tight_layout(); f.savefig(f"{OUT}/fig4_quality_vs_weight.png",dpi=140); plt.close(f)

# F5 writeback effect
f,a=plt.subplots(figsize=(6.4,4.2))
ws=[0.0,0.7,0.9]; x=range(len(ws)); wd=.35
a.bar([i-wd/2 for i in x],[tr("abrupt_shift",False,w)[39] for w in ws],wd,label="write-back OFF",color="#c0392b")
a.bar([i+wd/2 for i in x],[tr("abrupt_shift",True,w)[39] for w in ws],wd,label="write-back ON",color="#8e44ad")
a.set_xticks(list(x)); a.set_xticklabels([f"w={w}" for w in ws]); a.set_ylabel("quality @ c40")
a.set_title("Fig 5 — Write-back effect at matched deference"); a.legend(fontsize=8); a.grid(alpha=.3,axis="y")
f.tight_layout(); f.savefig(f"{OUT}/fig5_writeback_effect.png",dpi=140); plt.close(f)

# F6 interaction
f,a=plt.subplots(figsize=(6.4,4.2))
for wb,c,l,ws in [(False,"#c0392b","write-back OFF",[0.0,0.3,0.7,0.9]),(True,"#8e44ad","write-back ON",[0.0,0.7,0.9])]:
    a.plot(ws,[tr("abrupt_shift",wb,w)[39] for w in ws],"o-",lw=2,color=c,label=l)
a.annotate("write-back alone\nsaturates the effect",xy=(0.0,0.268),xytext=(0.25,0.45),
           arrowprops=dict(arrowstyle="->",color="k"),fontsize=8)
a.set_xlabel("deference weight w"); a.set_ylabel("quality @ c40")
a.set_title("Fig 6 — Interaction: deference x write-back"); a.legend(fontsize=8); a.grid(alpha=.3)
f.tight_layout(); f.savefig(f"{OUT}/fig6_interaction.png",dpi=140); plt.close(f)

# F7 adaptation time distribution
f,a=plt.subplots(figsize=(7.4,4.2))
labs=[];vals=[]
for wb in [False,True]:
    for w in ([0.0,0.3,0.7,0.9] if not wb else [0.0,0.7,0.9]):
        ts=[adapt(idx[("abrupt_shift",wb,w,s)]) for s in SEEDS]
        ok=[t for t in ts if t is not None]
        labs.append(f"{'ON' if wb else 'OFF'}\nw={w}"); vals.append(ok if ok else [])
pos=range(len(labs))
for i,v in enumerate(vals):
    if v: a.scatter([i]*len(v),v,color="#27ae60",zorder=3,label="adapted" if i==0 else "")
    else: a.scatter([i],[41],marker="x",color="#c0392b",s=70,zorder=3,label="censored (never adapted)" if i==1 else "")
a.set_xticks(list(pos)); a.set_xticklabels(labs,fontsize=8); a.set_ylabel("cycles to adapt (>=0.70 x3)")
a.axhline(41,ls=":",c="gray"); a.text(0.1,41.5,"censored",fontsize=7,color="gray")
a.set_title("Fig 7 — Adaptation time (10 seeds/condition)"); a.legend(fontsize=8); a.grid(alpha=.3,axis="y")
f.tight_layout(); f.savefig(f"{OUT}/fig7_adaptation_time.png",dpi=140); plt.close(f)
print("7 figures ->",OUT)
