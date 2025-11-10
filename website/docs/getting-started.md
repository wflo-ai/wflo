---
sidebar_position: 2
title: Getting Started
description: Quick start guide to building your first secure AI agent workflow
---

# Getting Started

Get up and running with Wflo in minutes.

## Prerequisites

- Python 3.11 or higher
- Docker (for sandbox execution)
- API keys for LLM providers (OpenAI, Anthropic, etc.)
- Git

## Installation

### From PyPI (Coming Soon)

```bash
pip install wflo
```

### From Source (Current)

```bash
# Clone the repository
git clone https://github.com/wflo-ai/wflo.git
cd wflo

# Install with Poetry
poetry install

# Or with pip
pip install -e ".[dev]"
```

### Verify Installation

```bash
wflo --version
```

## Your First Workflow

Create `workflow.py`:

```python
from wflo import Workflow

workflow = Workflow("hello-world")
workflow.set_budget(max_cost_usd=1.00)

@workflow.step
async def greet(context):
    """Simple greeting step"""
    name = context.inputs.get("name", "World")
    message = f"Hello, {name}!"
    context.logger.info("greeting_generated", message=message)
    return {"greeting": message}
```

Run it:

```bash
wflo run workflow.py --input name="Alice"
```

## Next Steps

- [Explore Features](./features.md) - Learn about all features
- [See Examples](./examples.md) - More code examples
- [Architecture](./architecture.md) - How Wflo works
