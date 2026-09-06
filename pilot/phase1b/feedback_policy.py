"""How much a producer defers to existing authoritative state."""

class FeedbackPolicy:
    """
    enabled=False : producer never reads state. No parents recorded.
    enabled=True  : producer reads prior state (parents ARE recorded, so the
                    provenance graph shows dependence) and copies the existing
                    majority with probability `confirmation_weight`, otherwise
                    uses its own fresh observation.

    weight 0.0 with enabled=True is a deliberate control: full provenance
    dependence, zero behavioural deference. It separates "RR detects a feedback
    edge" from "RR detects actual harm".
    """

    def __init__(self, cfg):
        self.enabled = cfg["enabled"]
        self.w = cfg.get("confirmation_weight", 0.0)

    def decide_value(self, own_obs, prior_values, rng):
        if not self.enabled or not prior_values:
            return own_obs
        if rng.random() < self.w:
            ones = sum(prior_values)
            return 1 if ones * 2 >= len(prior_values) else 0
        return own_obs
