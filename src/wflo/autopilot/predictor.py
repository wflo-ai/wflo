"""
Cost Prediction using Historical Data
"""

import json
from pathlib import Path
from typing import Dict, Optional


class CostPredictor:
    """Predict LLM call costs before execution using historical data."""

    def __init__(self):
        # Store history in user's home directory
        self.history_file = Path.home() / ".wflo" / "cost_history.json"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history = self._load_history()

    def predict(self, request_details: Dict) -> Optional[float]:
        """
        Predict cost based on similar past requests.

        Args:
            request_details: Normalized request details (model, messages, etc.)

        Returns:
            Predicted cost in USD, or None if no historical data
        """
        model = request_details.get("model")
        if not model:
            return None

        # Find similar past requests for this model
        model_history = [
            entry for entry in self.history if entry.get("model") == model
        ]

        if not model_history:
            return None  # No historical data for this model

        # Simple prediction: average cost for this model
        avg_cost = sum(entry["cost"] for entry in model_history) / len(model_history)

        # Adjust based on token count if available
        max_tokens = request_details.get("max_tokens")
        if max_tokens:
            # Scale based on requested tokens vs historical average
            avg_tokens = (
                sum(entry.get("max_tokens", 1000) for entry in model_history)
                / len(model_history)
            )
            if avg_tokens > 0:
                scale = max_tokens / avg_tokens
                return avg_cost * scale

        # Adjust based on message count
        messages = request_details.get("messages", [])
        if messages:
            avg_message_count = (
                sum(len(entry.get("messages", [])) for entry in model_history)
                / len(model_history)
            )
            if avg_message_count > 0:
                scale = len(messages) / avg_message_count
                return avg_cost * scale

        return avg_cost

    def learn(self, request_details: Dict, actual_cost: float):
        """
        Learn from actual execution to improve future predictions.

        Args:
            request_details: Request details
            actual_cost: Actual cost incurred
        """
        entry = {
            "model": request_details.get("model"),
            "cost": actual_cost,
            "max_tokens": request_details.get("max_tokens"),
            "messages": request_details.get("messages", []),
            "temperature": request_details.get("temperature"),
        }

        self.history.append(entry)

        # Keep only last 1000 entries to prevent file from growing too large
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

        self._save_history()

    def get_model_stats(self, model: str) -> Dict:
        """Get statistics for a specific model."""
        model_history = [entry for entry in self.history if entry["model"] == model]

        if not model_history:
            return {}

        costs = [entry["cost"] for entry in model_history]
        return {
            "model": model,
            "call_count": len(model_history),
            "avg_cost": sum(costs) / len(costs),
            "min_cost": min(costs),
            "max_cost": max(costs),
            "total_cost": sum(costs),
        }

    def _load_history(self) -> list:
        """Load historical data from disk."""
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save_history(self):
        """Save historical data to disk."""
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.history, f, indent=2)
        except IOError:
            # Fail silently if can't write (e.g., permissions issue)
            pass
