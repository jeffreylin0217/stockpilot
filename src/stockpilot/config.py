from dataclasses import dataclass
from pathlib import Path
import math
ROOT = Path(__file__).resolve().parents[2]
@dataclass(frozen=True)
class PlanningConfig:
    window_days: int = 28
    lead_time_days: int = 7
    review_days: int = 7
    z_score: float = 1.65

    def __post_init__(self):
        for name in ("window_days", "lead_time_days", "review_days"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.window_days < 2:
            raise ValueError("window_days must be at least 2 to estimate sample variability")
        if not math.isfinite(self.z_score) or self.z_score < 0:
            raise ValueError("z_score must be finite and nonnegative")
