# OpenAI Direct Integration with Wflo

This example shows how to use OpenAI SDK directly with Wflo for production-ready agent applications.

## What is OpenAI Direct Integration?

Many developers use the OpenAI SDK directly without any framework for maximum control and simplicity.

## Common Use Cases

- **Function calling agents**: Tool use with GPT-4
- **Assistants API**: OpenAI's native assistant framework
- **Simple chatbots**: Conversational applications
- **Code generation**: GitHub Copilot-style apps
- **Data analysis**: Analyze and transform data

## What Wflo Adds

| Vanilla OpenAI | With Wflo |
|----------------|-----------|
| Manual cost tracking | ✅ Automatic cost tracking |
| No budget limits | ✅ Hard budget enforcement |
| Manual retries | ✅ Auto-retry with backoff |
| Basic error handling | ✅ Circuit breakers |
| Limited observability | ✅ Full tracing + metrics |
| No state management | ✅ Checkpointing + rollback |

## Examples

- `basic_chat.py` - Simple chat WITHOUT wflo
- `wflo_wrapped_chat.py` - Same chat WITH wflo
- `function_calling_agent.py` - Tool use with cost tracking
- `assistants_api.py` - OpenAI Assistants with wflo
- `streaming_responses.py` - Streaming with budget enforcement
