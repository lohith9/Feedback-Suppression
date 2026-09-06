"""Single place that locates the frozen, validated Phase-1B engine.
The migration re-exports that engine so NEW behaviour == OLD behaviour by
construction; equivalence is then PROVEN by tests/test_reference_regression.py
against the 780 published raw runs. Frozen engine files are never edited."""
import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(_ROOT, "pilot"), os.path.join(_ROOT, "pilot", "phase1b")):
    if p not in sys.path:
        sys.path.insert(0, p)
ENGINE_ROOT = _ROOT
