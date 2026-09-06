"""Layer 1 — truth regimes. Re-export of the frozen TruthProcess."""
from .. import _engine_path  # noqa: F401
from truth_process import TruthProcess   # frozen: pilot/phase1b/truth_process.py
__all__ = ["TruthProcess"]
