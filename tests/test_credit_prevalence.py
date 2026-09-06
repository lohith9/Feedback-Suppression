"""Prevalence preserved (not forced to 50%); post-shift prevalence rises (downturn)."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT); sys.path.insert(0,os.path.dirname(__file__))
from src.scenarios.credit_risk import CreditRiskScenario
from _credit_fixture import make_fixture
def test_real_prevalence():
    fx=make_fixture(prevalence=0.22,seed=5)
    d=CreditRiskScenario(n_entities=400,seed=5,data_csv=fx).load().describe()
    assert d["native_prevalence"] is not None
    assert abs(d["baseline_prevalence"]-d["native_prevalence"])<0.06
    assert d["post_prevalence"]>=d["baseline_prevalence"]-1e-9, "downturn should not REDUCE defaults"
    assert 0.0 < d["flip_fraction"] < 0.9, "flip must be measured, non-trivial, non-total"
    print(f"real prevalence: native={d['native_prevalence']} baseline={d['baseline_prevalence']} "
          f"post={d['post_prevalence']} flip={d['flip_fraction']}")
def test_substrate_not_fifty():
    d=CreditRiskScenario(n_entities=400,seed=1).load().describe()
    assert not (0.45<=d["baseline_prevalence"]<=0.55), "substrate baseline must not be ~50%"
    print(f"substrate baseline prevalence ~{d['baseline_prevalence']} (not 50%)")
if __name__=="__main__": test_real_prevalence(); test_substrate_not_fifty(); print("PREVALENCE TESTS PASSED")
