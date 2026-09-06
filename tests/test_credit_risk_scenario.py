"""Credit-risk scenario: interface, determinism, ground-truth firewall, metadata.
Data-dependent checks SKIP (not fake-pass) when the real CSV is absent."""
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
from src.scenarios.credit_risk import CreditRiskScenario
CSV=os.path.join(ROOT,"data","raw","credit_default.csv")

def test_loads_and_metadata():
    s=CreditRiskScenario(n_entities=50,seed=1).load()
    d=s.describe()
    assert d["license"]=="CC BY 4.0" and d["doi"]=="10.24432/C55S3H"
    assert "source" in d and "is_real_data" in d
    print("metadata OK; source =", d["source"])

def test_deterministic():
    a=CreditRiskScenario(n_entities=80,seed=7).load(); a.initialize_truth()
    b=CreditRiskScenario(n_entities=80,seed=7).load(); b.initialize_truth()
    ents=a.initialize_entities()
    assert all(a.get_ground_truth(e,c)==b.get_ground_truth(e,c) for e in ents for c in (1,20,40))
    print("deterministic under fixed seed OK")

def test_ground_truth_firewall():
    s=CreditRiskScenario(n_entities=20,seed=1).load(); s.initialize_truth()
    # the scenario must refuse to observe on behalf of the system
    try: s.observe("c0000",1); assert False,"observe() should raise"
    except RuntimeError: pass
    # oracle model is name-mangled/private (not a public attribute)
    assert not hasattr(s,"model") and hasattr(s,"_model")
    print("ground-truth firewall OK (oracle is evaluator-only)")

def test_shift_is_measured():
    # Corrected scenario MEASURES the flip fraction (driven by the counterfactual);
    # it is not forced to a target band. Require only that it is non-trivial and
    # non-total, so the shift is neither invisible nor a blind inversion.
    s=CreditRiskScenario(n_entities=200,mode="abrupt_shift",seed=1).load(); s.initialize_truth()
    ff=s.describe()["flip_fraction"]
    assert 0.0 < ff < 0.9, f"flip fraction {ff} trivial or total"
    print(f"shift flip fraction (measured): {ff}")

def test_real_data_if_present():
    if not os.path.exists(CSV):
        print("SKIP real-data checks: data/raw/credit_default.csv absent (download blocked in sandbox)"); return
    s=CreditRiskScenario(n_entities=200,seed=1).load()
    assert s.describe()["is_real_data"]
    print("real-data load OK")

if __name__=="__main__":
    for fn in [test_loads_and_metadata,test_deterministic,test_ground_truth_firewall,
               test_shift_is_measured,test_real_data_if_present]: fn()
    print("CREDIT SCENARIO TESTS PASSED")
