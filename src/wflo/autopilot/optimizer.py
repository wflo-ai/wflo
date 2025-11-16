"""
Auto-Optimization for Cost Reduction
"""

from typing import Dict
from .config import WfloConfig


class CostOptimizer:
    """Automatically optimize LLM calls for cost while maintaining quality."""

    # Model cost tiers and fallbacks
    MODEL_TIERS = {
        # OpenAI models
        "gpt-4": {
            "cost_per_1k": 0.03,
            "tier": "premium",
            "fallbacks": ["gpt-4-turbo", "gpt-3.5-turbo"],
        },
        "gpt-4-turbo": {
            "cost_per_1k": 0.01,
            "tier": "standard",
            "fallbacks": ["gpt-3.5-turbo"],
        },
        "gpt-3.5-turbo": {
            "cost_per_1k": 0.0015,
            "tier": "budget",
            "fallbacks": [],
        },
        # Anthropic models
        "claude-3-opus-20240229": {
            "cost_per_1k": 0.015,
            "tier": "premium",
            "fallbacks": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        },
        "claude-3-sonnet-20240229": {
            "cost_per_1k": 0.003,
            "tier": "standard",
            "fallbacks": ["claude-3-haiku-20240307"],
        },
        "claude-3-haiku-20240307": {
            "cost_per_1k": 0.00025,
            "tier": "budget",
            "fallbacks": [],
        },
    }

    def __init__(self, config: WfloConfig):
        self.config = config

    def optimize(self, kwargs: dict, target_cost: float) -> dict:
        """
        Optimize request parameters to fit within target cost.

        Optimization strategies (in order):
        1. Switch to cheaper model if possible
        2. Reduce max_tokens
        3. Truncate context/messages
        4. Reduce temperature (less randomness = faster)

        Args:
            kwargs: Original request kwargs
            target_cost: Target cost in USD

        Returns:
            Optimized kwargs
        """
        optimized = kwargs.copy()

        # Strategy 1: Switch to cheaper model
        current_model = kwargs.get("model", "gpt-3.5-turbo")
        if current_model in self.MODEL_TIERS:
            tier_info = self.MODEL_TIERS[current_model]

            # If in premium or standard tier, try fallback
            if tier_info["tier"] in ["premium", "standard"] and tier_info["fallbacks"]:
                fallback_model = tier_info["fallbacks"][0]
                optimized["model"] = fallback_model
                if not self.config.silent:
                    print(f"   🔽 Model: {current_model} → {fallback_model}")

        # Strategy 2: Reduce max_tokens if set
        if "max_tokens" in kwargs:
            original_max = kwargs["max_tokens"]
            if original_max > 500:
                # Reduce by 50% but keep at least 100
                new_max = max(100, original_max // 2)
                optimized["max_tokens"] = new_max
                if not self.config.silent:
                    print(f"   🔽 Max tokens: {original_max} → {new_max}")

        # Strategy 3: Truncate long context
        if "messages" in kwargs:
            messages = kwargs["messages"]

            # Calculate total character count
            total_chars = sum(
                len(str(msg.get("content", ""))) for msg in messages
            )

            # If context is very long, keep only recent messages
            if total_chars > 10000 and len(messages) > 5:
                # Keep system message (if any) + last 4 messages
                system_msgs = [m for m in messages if m.get("role") == "system"]
                user_msgs = [m for m in messages if m.get("role") != "system"]

                optimized["messages"] = system_msgs + user_msgs[-4:]

                if not self.config.silent:
                    print(
                        f"   ✂️  Context: {len(messages)} messages → "
                        f"{len(optimized['messages'])} messages"
                    )

        # Strategy 4: Reduce temperature (faster inference)
        if "temperature" in kwargs and kwargs["temperature"] > 0.5:
            optimized["temperature"] = 0.5
            if not self.config.silent:
                print(f"   🎯 Temperature: {kwargs['temperature']} → 0.5")

        return optimized

    def get_cheaper_model(self, current_model: str) -> str:
        """
        Get the cheapest fallback model for a given model.

        Args:
            current_model: Current model name

        Returns:
            Cheaper model name, or original if no cheaper option
        """
        if current_model in self.MODEL_TIERS:
            tier_info = self.MODEL_TIERS[current_model]
            if tier_info["fallbacks"]:
                return tier_info["fallbacks"][-1]  # Return cheapest fallback

        return current_model

    def estimate_savings(
        self, original_kwargs: dict, optimized_kwargs: dict
    ) -> Dict[str, float]:
        """
        Estimate cost savings from optimization.

        Returns:
            Dict with original_cost, optimized_cost, savings
        """
        original_model = original_kwargs.get("model", "gpt-3.5-turbo")
        optimized_model = optimized_kwargs.get("model", "gpt-3.5-turbo")

        # Rough estimate based on model tiers
        original_tier = self.MODEL_TIERS.get(original_model, {})
        optimized_tier = self.MODEL_TIERS.get(optimized_model, {})

        original_cost_1k = original_tier.get("cost_per_1k", 0.001)
        optimized_cost_1k = optimized_tier.get("cost_per_1k", 0.001)

        # Assume average of 1000 tokens
        estimated_tokens = 1000
        original_cost = (original_cost_1k / 1000) * estimated_tokens
        optimized_cost = (optimized_cost_1k / 1000) * estimated_tokens

        return {
            "original_cost": original_cost,
            "optimized_cost": optimized_cost,
            "savings": original_cost - optimized_cost,
            "savings_pct": (
                ((original_cost - optimized_cost) / original_cost * 100)
                if original_cost > 0
                else 0
            ),
        }
