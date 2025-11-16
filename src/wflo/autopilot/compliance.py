"""
Compliance Checker - Approval Gates and Risk Assessment
"""

from typing import Dict, Optional
from .config import WfloConfig


class ComplianceChecker:
    """Check compliance rules and trigger approval gates for risky operations."""

    # Risk patterns (keywords that indicate risky operations)
    RISK_PATTERNS = {
        "critical": [
            "delete",
            "drop",
            "truncate",
            "remove",
            "destroy",
            "terminate",
        ],
        "high": [
            "update",
            "modify",
            "alter",
            "change",
            "write",
            "insert",
        ],
        "medium": [
            "read",
            "select",
            "query",
            "fetch",
        ],
    }

    # Compliance presets
    COMPLIANCE_PRESETS = {
        "hipaa": {
            "require_approval": True,
            "audit_all": True,
            "data_encryption": True,
            "min_risk_level": "medium",
        },
        "pci": {
            "require_approval": True,
            "audit_all": True,
            "data_encryption": True,
            "min_risk_level": "high",
        },
        "sox": {
            "require_approval": True,
            "audit_all": True,
            "min_risk_level": "critical",
        },
    }

    def __init__(self, config: WfloConfig):
        self.config = config
        self.preset = self.COMPLIANCE_PRESETS.get(config.compliance_mode, {})

    def check(self, request_details: Dict) -> Optional[Dict]:
        """
        Check if request requires approval.

        Args:
            request_details: Request details (model, messages, etc.)

        Returns:
            Approval requirement dict if approval needed, None otherwise
            Dict contains: reason, risk_level, operation
        """
        # Extract content from messages
        messages = request_details.get("messages", [])
        content = " ".join(
            str(msg.get("content", "")).lower()
            for msg in messages
            if isinstance(msg, dict)
        )

        # Check for risky patterns
        risk_level = self._assess_risk(content)

        # Check if approval required based on risk level
        if self._requires_approval(risk_level):
            return {
                "reason": f"Operation contains {risk_level}-risk patterns",
                "risk_level": risk_level,
                "operation": content[:100],  # First 100 chars
                "preset": self.config.compliance_mode,
            }

        return None

    def _assess_risk(self, content: str) -> str:
        """
        Assess risk level based on content.

        Returns:
            Risk level: critical, high, medium, low
        """
        content_lower = content.lower()

        # Check for critical patterns
        for pattern in self.RISK_PATTERNS["critical"]:
            if pattern in content_lower:
                return "critical"

        # Check for high patterns
        for pattern in self.RISK_PATTERNS["high"]:
            if pattern in content_lower:
                return "high"

        # Check for medium patterns
        for pattern in self.RISK_PATTERNS["medium"]:
            if pattern in content_lower:
                return "medium"

        return "low"

    def _requires_approval(self, risk_level: str) -> bool:
        """Check if risk level requires approval based on compliance preset."""
        if not self.preset:
            return False

        if not self.preset.get("require_approval"):
            return False

        min_risk = self.preset.get("min_risk_level", "critical")

        # Map risk levels to numeric values
        risk_values = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
        }

        return risk_values.get(risk_level, 0) >= risk_values.get(min_risk, 4)
