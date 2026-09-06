"""Shift timing + integrity: applied exactly at change_cycle; pre-shift unchanged;
flip measured not forced; truth consumes no RNG."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT); sys.path.insert(0,os.path.dirname(__file__))
from src.scenarios.credit_risk import CreditRiskScenario
def test_shift_timing_and_integrity():
    ch=15
    s=CreditRiskScenario(n_entities=200,mode="abrupt_shift",change_cycle=ch,seed=2).load(); t=s.initialize_truth()
    ents=s.initialize_entities()
    # pre-shift cycles identical to baseline (cycle 1); shift lands exactly at ch
    for e in ents:
        base=t.value(e,1)
        assert all(t.value(e,c)==base for c in range(1,ch)), "pre-shift truth changed early"
        assert t.value(e,ch)==t.value(e,ch+5), "post-shift truth unstable"
    # flip fraction measured from baseline vs post (not silently forced)
    flips=sum(1 for e in ents if t.value(e,ch-1)!=t.value(e,ch))
    assert flips==round(s.describe()["flip_fraction"]*len(ents))
    assert 0<flips<len(ents)
    print(f"shift lands at cycle {ch}; pre-shift stable; measured flips={flips}/{len(ents)}")
def test_no_rng_leak_and_determinism():
    a=CreditRiskScenario(n_entities=150,seed=9).load(); ta=a.initialize_truth()
    b=CreditRiskScenario(n_entities=150,seed=9).load(); tb=b.initialize_truth()
    ents=a.initialize_entities()
    # value() is pure: repeated calls + identical seeds => identical labels
    assert not hasattr(ta,"rng")
    assert all(ta.value(e,c)==tb.value(e,c) for e in ents for c in (1,14,15,40))
    print("truth.value is pure (no RNG), deterministic under seed")
if __name__=="__main__": test_shift_timing_and_integrity(); test_no_rng_leak_and_determinism(); print("SHIFT TESTS PASSED")
