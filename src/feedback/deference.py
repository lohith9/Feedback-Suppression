"""Layer 3 — Factor A: producer deference (behavioural feedback).
Re-export of the frozen FeedbackPolicy. Knob: deference weight w in [0,1]."""
from .. import _engine_path  # noqa: F401
from feedback_policy import FeedbackPolicy   # frozen: pilot/phase1b/feedback_policy.py
__all__ = ["FeedbackPolicy"]
