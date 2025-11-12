# LangGraph Integration with Wflo

This example shows how to use LangGraph with Wflo for production-ready agent orchestration.

## What is LangGraph?

LangGraph is a low-level orchestration framework for building stateful, graph-based AI agents. Used by companies like:
- Klarna (85M users, 80% faster resolution)
- LinkedIn, Uber, Replit, Elastic

## Key Features LangGraph Provides

- **Stateful workflows**: Persist state across steps
- **Graph-based execution**: Nodes and edges for complex flows
- **Human-in-the-loop**: Pause and resume with human input
- **Built-in memory**: Conversation history and context

## What Wflo Adds on Top

| LangGraph Feature | Wflo Enhancement |
|-------------------|------------------|
| State persistence | ✅ Automatic checkpointing with rollback |
| Execution | ✅ Cost tracking per node |
| Human-in-loop | ✅ Budget enforcement + approval gates |
| Error handling | ✅ Circuit breakers + retry with backoff |
| Observability | ✅ Enhanced tracing + metrics |

## Use Cases

1. **Customer Support Bot** (like Klarna)
2. **Research Assistant** with multi-step reasoning
3. **Code Review Agent** with human approval
4. **Data Pipeline** with conditional logic

## Examples

- `basic_graph.py` - Simple LangGraph workflow WITHOUT wflo
- `wflo_wrapped_graph.py` - Same workflow WITH wflo integration
- `customer_support_bot.py` - Production example with cost limits
- `research_assistant.py` - Multi-agent research with approvals
