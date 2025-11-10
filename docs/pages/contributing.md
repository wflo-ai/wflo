---
layout: default
title: Contributing
description: "How to contribute to Wflo - the secure runtime for AI agents"
---

<div class="container" style="margin-top: 3rem;">

# Contributing to Wflo

Thank you for your interest in contributing to Wflo! We're building the secure runtime for AI agents, and we welcome contributions from the community.

---

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a branch** for your changes
4. **Make your changes** and commit them
5. **Push to your fork** and submit a pull request

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Docker (for sandbox testing)
- Git
- Poetry (optional, for dependency management)

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/wflo-ai/wflo.git
cd wflo

# Install dependencies with Poetry
poetry install --with dev

# Or with pip
pip install -e ".[dev]"

# Verify installation
python -c "import wflo; print(wflo.__version__)"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=wflo --cov-report=html

# Run specific test file
pytest tests/unit/test_workflow_models.py

# Run with verbose output
pytest -v
```

### Code Quality Checks

```bash
# Format code with black
black src/ tests/

# Sort imports
isort src/ tests/

# Run linter
ruff check src/ tests/

# Type checking
mypy src/
```

---

## How Can You Contribute?

### 1. Code Contributions

We're actively building the following components:

| Component | Status | Good First Issue |
|:----------|:-------|:-----------------|
| Core Workflow Engine | 🚧 In Progress | ✅ Yes |
| Sandbox Runtime | 📋 Planned | ❌ Complex |
| Approval Gates | 📋 Planned | ✅ Yes |
| Cost Management | 📋 Planned | ✅ Yes |
| Observability | 📋 Planned | ❌ Complex |
| Rollback System | 📋 Planned | ❌ Complex |

Check out our [Issues](https://github.com/wflo-ai/wflo/issues) to see what we're working on.

**Good First Issues**: Look for issues labeled `good-first-issue` - these are great for new contributors!

---

### 2. Documentation

Documentation is just as important as code! Ways to contribute:

- **Improve the README**: Clarify explanations, fix typos
- **Write tutorials**: Create step-by-step guides
- **Create examples**: Share real-world use cases
- **API documentation**: Document functions and classes
- **Fix broken links**: Keep docs up to date

---

### 3. Testing

Help us build a robust test suite:

- **Write unit tests**: Test individual components
- **Create integration tests**: Test component interactions
- **Test edge cases**: Find and fix corner cases
- **Performance testing**: Benchmark and optimize
- **Report bugs**: File detailed bug reports

---

### 4. Ideas and Feedback

Your input is valuable:

- **Feature requests**: Open issues for new features
- **Use case sharing**: Tell us how you use Wflo
- **API feedback**: Suggest API improvements
- **Join discussions**: Participate in design discussions

---

## Code Style

We follow standard Python conventions with strict type checking.

### Python Style Guide

```python
# Good example
from typing import Optional
from dataclasses import dataclass

@dataclass
class WorkflowConfig:
    """Configuration for a workflow.

    Attributes:
        name: Unique name for the workflow
        version: Semantic version string
        budget: Optional budget limit in USD
    """

    name: str
    version: str
    budget: Optional[float] = None

async def execute_workflow(
    workflow_id: str,
    context: WorkflowContext,
    *,
    budget: Optional[float] = None,
) -> WorkflowResult:
    """Execute a workflow with optional budget limit.

    Args:
        workflow_id: Unique identifier for the workflow
        context: Execution context with state and config
        budget: Optional maximum cost in USD

    Returns:
        WorkflowResult containing execution status and outputs

    Raises:
        BudgetExceededError: If execution exceeds budget
        WorkflowError: If execution fails
    """
    pass
```

### Style Rules

- **PEP 8**: Follow PEP 8 for code style
- **Type hints**: All function signatures must have type hints
- **Docstrings**: All public APIs must have docstrings (Google style)
- **Black**: Use Black for code formatting (line length: 100)
- **isort**: Use isort for import sorting
- **mypy**: Pass mypy strict type checking

### Running Style Checks

```bash
# Format code
make format

# Check code style
make lint

# Type check
make typecheck

# All checks
make check
```

---

## Commit Messages

Write clear, descriptive commit messages following conventional commits.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semicolons, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Changes to build process or auxiliary tools

### Examples

```bash
# Good commit messages
feat(workflow): add support for conditional step execution

fix(sandbox): prevent memory leak in container cleanup

docs(api): add examples for approval gate configuration

test(cost): add unit tests for cost tracking

# Bad commit messages
fix bug
update code
changes
```

### Detailed Example

```
feat(cost): add multi-provider cost tracking

- Implement CostTracker class with provider-specific pricing
- Add integration with OpenAI, Anthropic, and Cohere APIs
- Include tests for cost calculation accuracy
- Update documentation with usage examples

Closes #123
```

---

## Pull Request Process

### Before Submitting

- [ ] Update documentation if you're changing functionality
- [ ] Add tests for new features
- [ ] Ensure all tests pass (`pytest`)
- [ ] Run code quality checks (`make check`)
- [ ] Update CHANGELOG.md (if applicable)
- [ ] Reference related issues in PR description

### PR Template

When you create a PR, use this template:

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Motivation
Why is this change needed? What problem does it solve?

## Testing
Describe how you tested your changes:
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have updated the CHANGELOG.md (if needed)

## Related Issues
Closes #123
Fixes #456
Related to #789
```

### Review Process

1. **Automated checks**: CI runs tests, linting, type checking
2. **Code review**: Maintainers review your code
3. **Feedback**: Address any comments or requested changes
4. **Approval**: Once approved, maintainers will merge
5. **Celebrate**: Your contribution is now part of Wflo! 🎉

---

## Architecture Decisions

For significant changes, we follow an Architecture Decision Record (ADR) process:

### ADR Process

1. **Open an issue** describing the problem
2. **Propose a solution** with alternatives considered
3. **Get feedback** from maintainers
4. **Document the decision** in `/docs/adr/`

### ADR Template

```markdown
# ADR-XXX: Title

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
What is the issue we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing?

## Consequences
What becomes easier or more difficult to do because of this change?

## Alternatives Considered
What other options did we consider?
```

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all.

### Our Standards

**Positive behavior includes:**
- Being respectful and inclusive
- Accepting constructive criticism gracefully
- Focusing on what's best for the community
- Showing empathy towards others

**Unacceptable behavior includes:**
- Harassment or discriminatory language
- Trolling or insulting comments
- Publishing others' private information
- Unprofessional conduct

### Enforcement

Instances of unacceptable behavior may be reported to the project maintainers at [conduct@wflo.ai](mailto:conduct@wflo.ai). All complaints will be reviewed and investigated promptly and fairly.

---

## Development Workflow

### Branch Naming

Use descriptive branch names:

```bash
# Feature branches
git checkout -b feat/add-approval-gates

# Bug fix branches
git checkout -b fix/sandbox-memory-leak

# Documentation branches
git checkout -b docs/update-api-reference
```

### Development Cycle

1. **Pick an issue** from the [issue tracker](https://github.com/wflo-ai/wflo/issues)
2. **Create a branch** from `main`
3. **Write code** with tests
4. **Commit** with clear messages
5. **Push** to your fork
6. **Open PR** against `main`
7. **Address feedback** from reviewers
8. **Merge** once approved

---

## Testing Guidelines

### Test Structure

```python
# tests/unit/test_feature.py
import pytest
from wflo.feature import MyFeature

class TestMyFeature:
    """Tests for MyFeature."""

    def test_basic_functionality(self):
        """Test basic functionality works."""
        feature = MyFeature()
        result = feature.do_something()
        assert result == expected

    def test_error_handling(self):
        """Test error handling."""
        feature = MyFeature()
        with pytest.raises(ValueError):
            feature.do_something_invalid()

    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test async operation."""
        feature = MyFeature()
        result = await feature.do_async_something()
        assert result is not None
```

### Test Coverage

Aim for high test coverage:

```bash
# Run with coverage report
pytest --cov=wflo --cov-report=html

# View coverage report
open htmlcov/index.html
```

Target: 80% code coverage for new code.

---

## Documentation Guidelines

### Docstring Format

We use Google-style docstrings:

```python
def complex_function(
    arg1: str,
    arg2: int,
    *,
    kwarg1: bool = False
) -> Dict[str, Any]:
    """One-line summary of the function.

    More detailed explanation if needed. This can span
    multiple lines and paragraphs.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        kwarg1: Description of kwarg1. Defaults to False.

    Returns:
        Dictionary with keys:
        - 'result': The main result
        - 'metadata': Additional metadata

    Raises:
        ValueError: If arg2 is negative
        TypeError: If arg1 is not a string

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result['result'])
        'test-42'
    """
    pass
```

---

## Release Process

Releases are managed by maintainers:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag: `git tag v0.1.0`
4. Push tag: `git push origin v0.1.0`
5. GitHub Actions builds and publishes to PyPI
6. Create GitHub release with changelog

---

## Questions?

- **GitHub Discussions**: [Ask questions](https://github.com/wflo-ai/wflo/discussions)
- **Issues**: [Report bugs or request features](https://github.com/wflo-ai/wflo/issues)
- **Discord**: Join our community (coming soon)
- **Email**: [dev@wflo.ai](mailto:dev@wflo.ai)

---

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

---

**Thank you for helping make Wflo better!**

We appreciate every contribution, no matter how small. Every bug report, feature request, documentation improvement, and code contribution helps make Wflo more robust and useful for everyone.
</div>
