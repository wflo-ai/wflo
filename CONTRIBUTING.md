# Contributing to Wflo

Thank you for your interest in contributing to Wflo! We're building the secure runtime for AI agents, and we welcome contributions from the community.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a branch** for your changes
4. **Make your changes** and commit them
5. **Push to your fork** and submit a pull request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/wflo-ai/wflo.git
cd wflo

# Install dependencies (coming soon)
# pip install -e ".[dev]"

# Run tests (coming soon)
# pytest
```

## How Can You Contribute?

### 1. Code Contributions

We're actively building the following components:

- **Core Workflow Engine** - Orchestration and execution logic
- **Sandbox Runtime** - Secure container execution
- **Approval Gates** - Human-in-the-loop workflows
- **Cost Management** - Budget tracking and enforcement
- **Observability** - Traces, metrics, and logs
- **Rollback System** - State snapshots and recovery

Check out our [Issues](https://github.com/wflo-ai/wflo/issues) to see what we're working on.

### 2. Documentation

- Improve the README
- Write tutorials and guides
- Create examples and use cases
- Fix typos and clarify explanations

### 3. Testing

- Write unit tests
- Create integration tests
- Test edge cases
- Report bugs

### 4. Ideas and Feedback

- Open issues for feature requests
- Share your use cases
- Provide feedback on APIs and design
- Join discussions

## Code Style

We follow standard Python conventions:

- **PEP 8** for Python code style
- **Type hints** for all function signatures
- **Docstrings** for all public APIs
- **Black** for code formatting
- **isort** for import sorting

```python
# Good example
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

## Commit Messages

Write clear, descriptive commit messages:

```
Add cost tracking for LLM API calls

- Implement CostTracker class with provider-specific pricing
- Add integration with OpenAI, Anthropic, and Cohere APIs
- Include tests for cost calculation accuracy
- Update documentation with usage examples

Closes #123
```

**Format:**
- First line: Short summary (50 chars or less)
- Blank line
- Detailed explanation if needed
- Reference related issues

## Pull Request Process

1. **Update documentation** if you're changing functionality
2. **Add tests** for new features
3. **Ensure all tests pass** before submitting
4. **Update the CHANGELOG** (if applicable)
5. **Reference related issues** in your PR description

### PR Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested your changes.

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have added tests for my changes
- [ ] All tests pass locally
- [ ] I have updated the documentation
- [ ] I have added an entry to the CHANGELOG (if needed)

## Related Issues
Closes #123
```

## Architecture Decisions

For significant changes, we follow an Architecture Decision Record (ADR) process:

1. Open an issue describing the problem
2. Propose a solution with alternatives considered
3. Get feedback from maintainers
4. Document the decision in `/docs/adr/`

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

Instances of unacceptable behavior may be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

## Questions?

- **GitHub Discussions**: Ask questions in [Discussions](https://github.com/wflo-ai/wflo/discussions)
- **Issues**: Report bugs or request features in [Issues](https://github.com/wflo-ai/wflo/issues)
- **Discord**: Join our community (coming soon)

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

---

Thank you for helping make Wflo better! 🚀
