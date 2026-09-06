"""Layer 1 — Scenario abstract interface (frozen ARCHITECTURE_DESIGN.md §1)."""
from abc import ABC, abstractmethod
class Scenario(ABC):
    name = "abstract"
    @abstractmethod
    def observe(self, entity, cycle): ...
    @abstractmethod
    def get_ground_truth(self, entity, cycle): ...
    @abstractmethod
    def apply_environment_change(self, cycle): ...
    def describe(self): return {"name": self.name}
