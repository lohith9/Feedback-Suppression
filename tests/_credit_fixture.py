"""Tiny SYNTHETIC fixture CSV to exercise the REAL code path (_build_real).
This is a UNIT-TEST FIXTURE, not the UCI dataset. Written to /tmp; never to
data/raw, so it can never masquerade as real UCI data."""
import csv, os, random, tempfile
def make_fixture(n=2000, prevalence=0.22, seed=1):
    rng = random.Random(seed)
    path = os.path.join(tempfile.gettempdir(), f"credit_fixture_{seed}.csv")
    feats = ["PAY_0","PAY_2","PAY_3","PAY_4","PAY_5","PAY_6","LIMIT_BAL"]
    with open(path,"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=feats+["default payment next month"]); w.writeheader()
        for _ in range(n):
            row={fe:(rng.randint(-1,8) if fe.startswith("PAY") else rng.randint(10000,500000)) for fe in feats}
            # native label loosely correlated with delinquency, at target prevalence
            score=sum(row[p] for p in feats[:6]) - row["LIMIT_BAL"]/100000
            row["default payment next month"]=1 if rng.random() < prevalence*(1+0.15*(score>3)) else 0
            w.writerow(row)
    return path
