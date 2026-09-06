"""Layer 4 — provenance instrumentation (READ-ONLY).
why-provenance ancestry + AOD/RR. These are pure graph reads over StateStore:
they consume NO system RNG and mutate NO state. That property is what
tests/test_non_interference.py verifies, and it is why they are classified as
instrumentation rather than part of the system under test."""
from .store import StateStore

def ancestry(store, aid):            return store.ancestry(aid)
def aod_rr(store, aid):              return store.aod_rr(aid)          # (AOD, RR, ancestry_size)
def propagation_depth(store, aid):  return store.max_depth(aid)
__all__ = ["ancestry", "aod_rr", "propagation_depth"]
