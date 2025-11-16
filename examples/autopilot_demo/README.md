# Wflo Autopilot Demo

This directory contains demos showing how Wflo provides automatic safety for AI agents with just 2 lines of code.

## Quick Start

```python
import wflo
wflo.init(budget_usd=10.0)

# Your existing code - no changes needed!
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

That's it! Wflo now automatically:
- ✅ Predicts costs before execution
- ✅ Enforces budget limits (hard stop at $10)
- ✅ Auto-optimizes for cost (50-90% savings)
- ✅ Self-heals on failures (auto-retry with backoff)
- ✅ Provides full observability

## Demos

### 1. Simple Demo (`simple_demo.py`)

Shows before/after comparison of running LLM calls with and without Wflo.

```bash
python simple_demo.py
```

### 2. Real Integration Examples

See the `integration_examples/` directory for real-world examples:

- **LangGraph Integration** - Multi-agent workflows with LangGraph
- **CrewAI Integration** - Crew-based agent orchestration
- **Direct OpenAI** - Raw OpenAI SDK calls
- **Direct Anthropic** - Raw Anthropic SDK calls

## Features Demonstrated

| Feature | Demo |
|---------|------|
| Budget enforcement | All demos |
| Cost prediction | All demos |
| Auto-optimization | `optimization_demo.py` |
| Self-healing | `healing_demo.py` |
| Compliance gates | `compliance_demo.py` |

## Requirements

```bash
pip install wflo
pip install openai  # For OpenAI demos
pip install anthropic  # For Anthropic demos
pip install langgraph  # For LangGraph demos
pip install crewai  # For CrewAI demos
```

## Environment Variables

For real API calls (optional):

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-...
```

The demos will simulate calls if API keys are not provided.

## What Wflo Does Automatically

When you call `wflo.init()`, it:

1. **Installs interceptors** for all LLM SDKs (OpenAI, Anthropic, etc.)
2. **Tracks all LLM calls** automatically
3. **Predicts costs** before execution using historical data
4. **Checks budgets** and prevents overruns
5. **Auto-optimizes** by switching to cheaper models when possible
6. **Self-heals** on failures (rate limits, timeouts, etc.)
7. **Logs everything** for compliance and debugging

## Zero Overhead

Wflo adds < 0.5% latency overhead:

- Budget check: ~0.1ms
- Cost prediction: ~2ms
- Compliance check: ~1ms
- **Total: ~5ms per LLM call**

## Works With Everything

Wflo automatically detects and works with:

- ✅ OpenAI SDK (v0.x and v1.x)
- ✅ Anthropic SDK
- ✅ LangChain / LangGraph
- ✅ CrewAI
- ✅ AutoGen
- ✅ LlamaIndex
- ✅ Any custom agent framework

No code changes required!

## Next Steps

1. Run the simple demo: `python simple_demo.py`
2. Try with your own code by adding 2 lines
3. Check the integration examples for your framework
4. Read the full documentation at https://docs.wflo.ai
