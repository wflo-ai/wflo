---
sidebar_position: 5
title: Examples
description: Code examples for building workflows
---

# Examples

Practical code examples to help you build AI agent workflows.

## Hello World

```python
from wflo import Workflow

workflow = Workflow("hello-world")

@workflow.step
async def greet(context):
    name = context.inputs.get("name", "World")
    return {"message": f"Hello, {name}!"}

__workflow__ = workflow
```

## With Budget Control

```python
workflow = Workflow("budget-controlled")
workflow.set_budget(max_cost_usd=10.00)

@workflow.step
async def expensive_operation(context):
    result = await context.llm.complete(
        model="gpt-4",
        prompt=context.inputs["prompt"]
    )
    return {"result": result.text}
```

## With Approval Gates

```python
@workflow.step(
    approval=ApprovalPolicy(required=True, approvers=["admin"])
)
async def delete_data(context):
    await context.db.execute("DELETE FROM records WHERE ...")
    return {"deleted": True}
```

[See more examples →](https://github.com/wflo-ai/wflo/blob/main/docs/pages/examples.md)
