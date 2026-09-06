"""Layer 6 — descriptive provenance metrics. AOD/RR are DESCRIPTIVE ONLY.
Standing constraint (frozen): they are NOT validated harm detectors (RQ4 negative)."""
def aod_at(rows, cycle):
    for r in rows:
        if r["cycle"] == cycle:
            return r["AOD"]
    return None
def rr_at(rows, cycle):
    for r in rows:
        if r["cycle"] == cycle:
            return r["RR"]
    return None
__all__ = ["aod_at", "rr_at"]
