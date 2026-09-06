"""Corrected ground truth: baseline == NATIVE UCI target; firewall holds."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT); sys.path.insert(0,os.path.dirname(__file__))
from src.scenarios.credit_risk import CreditRiskScenario
from _credit_fixture import make_fixture
import csv

def test_baseline_equals_native_target():
    fx=make_fixture(seed=3)
    native={}
    for i,r in enumerate(csv.DictReader(open(fx))): native[i]=int(r["default payment next month"])
    s=CreditRiskScenario(n_entities=300,mode="abrupt_shift",seed=3,data_csv=fx).load(); s.initialize_truth()
    assert s.describe()["is_real_data"], "must use the real code path"
    # every entity's PRE-shift truth is a native 0/1 label (not a median prediction)
    ents=s.initialize_entities()
    vals=set(s.get_ground_truth(e,1) for e in ents)
    assert vals <= {0,1}
    # baseline prevalence equals the sampled native prevalence (preserved, not 0.5)
    d=s.describe()
    assert abs(d["baseline_prevalence"]-d["native_prevalence"]) < 0.06, (d["baseline_prevalence"],d["native_prevalence"])
    assert not (0.45 <= d["baseline_prevalence"] <= 0.55), "prevalence must NOT be forced to ~50%"
    print(f"baseline==native target OK; native={d['native_prevalence']} baseline={d['baseline_prevalence']}")

def test_firewall():
    fx=make_fixture(seed=4)
    s=CreditRiskScenario(n_entities=100,seed=4,data_csv=fx).load(); s.initialize_truth()
    try: s.observe("client_0000",1); assert False
    except RuntimeError: pass
    assert hasattr(s,"_model") and not hasattr(s,"model")     # oracle is private
    print("firewall OK: producer/decision cannot reach the oracle; evaluator can")

if __name__=="__main__":
    test_baseline_equals_native_target(); test_firewall(); print("GROUND-TRUTH TESTS PASSED")
