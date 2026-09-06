"""Layer 1 — controlled reference scenario (the current C1/C2 synthetic task).
Thin descriptor over the frozen engine; the canonical run loop remains Sim1C/
SimC2 so behaviour is identical. Public-data scenarios (credit risk) will
subclass scenarios.base.Scenario later — NOT in this migration."""
from .. import _engine_path  # noqa: F401
from sim1c import make_cfg as c1_cfg      # frozen
from sim_c2 import cfg_c2 as c2_cfg        # frozen
class SyntheticScenario:
    name = "synthetic"
    def describe(self):
        return {"name": self.name, "entities": 100, "task": "binary",
                "source": "controlled reference (C1/C2)"}
__all__ = ["SyntheticScenario", "c1_cfg", "c2_cfg"]
