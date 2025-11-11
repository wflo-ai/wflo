# Wflo Examples

This directory contains working examples demonstrating how to use Wflo for AI agent workflows.

## Available Examples

### 1. Simple LLM Agent ([simple_llm_agent/](./simple_llm_agent/))

A complete end-to-end example showing:
- OpenAI GPT-4 integration
- Automatic cost tracking
- Database persistence
- Event streaming to Kafka
- Error handling and logging

**Use Case**: Basic LLM agent that answers questions with cost governance.

**Prerequisites**:
- OpenAI API key
- Docker and Docker Compose
- PostgreSQL, Redis, Kafka running

**Quick Start**:
```bash
# 1. Set API key
export OPENAI_API_KEY="sk-..."

# 2. Start infrastructure
docker compose up -d

# 3. Run example
poetry run python examples/simple_llm_agent/run.py --prompt "What is 2+2?"
```

## Example Structure

Each example follows this structure:

```
example_name/
├── README.md          # Detailed example documentation
├── workflow.py        # Workflow definition
├── run.py            # Execution script
├── .env.example      # Environment variables template
└── tests/            # Example-specific tests (optional)
```

## Coming Soon

- **Multi-Step Agent**: Chain multiple LLM calls with state management
- **Sandbox Execution**: Execute untrusted code safely
- **Human Approval**: Workflow with approval gates
- **Cost-Optimized Agent**: Smart model selection based on budget
- **Multi-Agent**: Parallel agent execution with coordination

## Contributing Examples

To add a new example:

1. Create a new directory in `examples/`
2. Follow the standard structure above
3. Include comprehensive README with:
   - What the example demonstrates
   - Prerequisites
   - Setup instructions
   - Expected output
4. Test thoroughly before submitting

## Support

For questions or issues with examples:
- Check the main [documentation](../docs/)
- Open an issue on GitHub
- Join our community discussions

---

*Last Updated: 2025-11-11*
