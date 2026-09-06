"""Credit-risk non-interference: instrumentation ON/OFF => identical system behaviour."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
from src.scenarios.credit_risk import CreditRiskScenario
from src.experiments.controller import run_credit_condition
def test_ni():
    checked=0
    for tm in ["static","abrupt_shift"]:
        for wb,w in [(False,0.0),(False,0.7),(True,0.0)]:
            for seed in range(1,6):
                sc=lambda: CreditRiskScenario(n_entities=100,mode=tm,seed=seed).load()
                on=run_credit_condition(sc(),w,wb,seed,instrument=True)
                off=run_credit_condition(sc(),w,wb,seed,instrument=False)
                for a,b in zip(on,off):
                    assert a["quality"]==b["quality"] and a["writes"]==b["writes"] \
                        and a["observations"]==b["observations"] and a["cum_regret"]==b["cum_regret"]
                checked+=1
    print(f"credit non-interference OK: {checked} conditions identical ON vs OFF")
if __name__=="__main__": test_ni(); print("PASSED")
