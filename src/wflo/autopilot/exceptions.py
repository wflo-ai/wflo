"""
Wflo Exceptions
"""


class WfloError(Exception):
    """Base exception for all Wflo errors."""
    pass


class BudgetExceededError(WfloError):
    """Raised when budget limit is exceeded."""

    def __init__(self, message: str, spent: float = None, budget: float = None):
        super().__init__(message)
        self.spent = spent
        self.budget = budget


class ApprovalDeniedError(WfloError):
    """Raised when human approval is denied."""

    def __init__(self, message: str, operation: str = None):
        super().__init__(message)
        self.operation = operation


class ComplianceViolationError(WfloError):
    """Raised when a compliance rule is violated."""

    def __init__(self, message: str, rule: str = None, severity: str = None):
        super().__init__(message)
        self.rule = rule
        self.severity = severity


class InterceptorError(WfloError):
    """Raised when interceptor installation fails."""
    pass


class PredictionError(WfloError):
    """Raised when cost prediction fails."""
    pass


class OptimizationError(WfloError):
    """Raised when auto-optimization fails."""
    pass


class HealingError(WfloError):
    """Raised when self-healing fails."""
    pass
