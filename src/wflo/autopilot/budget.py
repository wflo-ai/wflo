"""
Budget Tracking and Enforcement
"""

from .exceptions import BudgetExceededError


class BudgetTracker:
    """Track and enforce budget limits with hard stops."""

    def __init__(self, budget_usd: float):
        self.budget_usd = budget_usd
        self.spent_usd = 0.0
        self.call_count = 0

    def remaining(self) -> float:
        """Get remaining budget in USD."""
        return max(0.0, self.budget_usd - self.spent_usd)

    def add(self, cost: float):
        """
        Add cost to spent budget and check limit.

        Raises:
            BudgetExceededError: If cost exceeds remaining budget
        """
        self.spent_usd += cost
        self.call_count += 1

        if self.spent_usd > self.budget_usd:
            raise BudgetExceededError(
                f"Budget exceeded: ${self.spent_usd:.2f} > ${self.budget_usd:.2f}",
                spent=self.spent_usd,
                budget=self.budget_usd,
            )

    def reset(self):
        """Reset budget tracking."""
        self.spent_usd = 0.0
        self.call_count = 0

    def get_stats(self) -> dict:
        """Get budget statistics."""
        return {
            "budget_usd": self.budget_usd,
            "spent_usd": self.spent_usd,
            "remaining_usd": self.remaining(),
            "utilization_pct": (self.spent_usd / self.budget_usd * 100)
            if self.budget_usd > 0
            else 0,
            "call_count": self.call_count,
            "avg_cost_per_call": (self.spent_usd / self.call_count)
            if self.call_count > 0
            else 0,
        }
