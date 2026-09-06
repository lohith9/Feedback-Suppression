"""Layer 3 — Factor B: decision write-back readability (architectural feedback).
Semantics (frozen in Sim1C.decide): the decision is ALWAYS written; readable
writes to attribute 'risk_level' (re-read as evidence), inert writes to
'decision_archive' (never read). Identical write count either way — this is what
isolates readability from write volume (the invariant C4)."""
READABLE_ATTR = "risk_level"
INERT_ATTR = "decision_archive"
def target_attribute(readable: bool) -> str:
    return READABLE_ATTR if readable else INERT_ATTR
__all__ = ["READABLE_ATTR", "INERT_ATTR", "target_attribute"]
