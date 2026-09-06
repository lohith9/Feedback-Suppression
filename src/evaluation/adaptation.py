"""Layer 6 — adaptation metrics (frozen thresholds live in preregistration YAML)."""
def adaptation_time(rows, change_cycle=15, threshold=0.70, persistence=3):
    post = [r for r in rows if r["cycle"] >= change_cycle]
    for i in range(len(post) - persistence + 1):
        if all(post[i + k]["quality"] >= threshold for k in range(persistence)):
            return post[i]["cycle"] - change_cycle
    return None
def quality_at(rows, cycle):
    for r in rows:
        if r["cycle"] == cycle:
            return r["quality"]
    return None
__all__ = ["adaptation_time", "quality_at"]
