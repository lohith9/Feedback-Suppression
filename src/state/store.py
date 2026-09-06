"""Layer 2 — Structured State Store. Re-exports the frozen StateStore/Assertion.
These are pure data structures (no RNG, no I/O); moving them is behaviour-neutral."""
from .. import _engine_path  # noqa: F401  (bootstraps path to frozen engine)
from sim import StateStore, Assertion   # frozen: pilot/sim.py
__all__ = ["StateStore", "Assertion"]
