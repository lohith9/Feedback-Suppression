"""Ground-truth processes. The evaluator knows truth; agents never see it."""

class TruthProcess:
    """Modes: static | abrupt_shift | multi_shift | gradual_drift."""

    def __init__(self, cfg, rng, entities):
        self.mode = cfg["mode"]
        self.cfg = cfg
        self.base = {e: rng.randint(0, 1) for e in entities}
        self.rng = rng
        # For gradual drift: per-entity flip schedule spread over a window.
        if self.mode == "gradual_drift":
            start = cfg.get("change_cycle", 15)
            width = cfg.get("drift_width", 10)
            self.flip_at = {e: start + rng.randint(0, max(1, width) - 1)
                            for e in entities}

    def value(self, entity, cycle):
        v = self.base[entity]
        if self.mode == "static":
            return v
        if self.mode == "abrupt_shift":
            return 1 - v if cycle >= self.cfg.get("change_cycle", 15) else v
        if self.mode == "multi_shift":
            flips = sum(1 for c in self.cfg.get("change_cycles", [10, 20]) if cycle >= c)
            return v if flips % 2 == 0 else 1 - v
        if self.mode == "gradual_drift":
            return 1 - v if cycle >= self.flip_at[entity] else v
        raise ValueError(self.mode)

    def change_cycles(self):
        if self.mode == "abrupt_shift":
            return [self.cfg.get("change_cycle", 15)]
        if self.mode == "multi_shift":
            return list(self.cfg.get("change_cycles", [10, 20]))
        if self.mode == "gradual_drift":
            return [self.cfg.get("change_cycle", 15)]
        return []
