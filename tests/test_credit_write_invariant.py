"""Credit-risk write-volume invariant: readable vs inert write-back => equal writes."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
from src.scenarios.credit_risk import CreditRiskScenario
from src.experiments.controller import run_credit_condition
def test_wi():
    for tm in ["static","abrupt_shift"]:
        for w in [0.0,0.7]:
            for seed in range(1,6):
                off=run_credit_condition(CreditRiskScenario(n_entities=100,mode=tm,seed=seed).load(),w,False,seed)[-1]["writes"]
                on =run_credit_condition(CreditRiskScenario(n_entities=100,mode=tm,seed=seed).load(),w,True ,seed)[-1]["writes"]
                assert off==on, f"WRITE-VOLUME VIOLATED {tm} w={w} s={seed}: {off} vs {on}"
    print("credit write-volume invariant OK (readable == inert)")
if __name__=="__main__": test_wi(); print("PASSED")
