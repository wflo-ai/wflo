# Anthropic Claude Integration with Wflo

This example shows how to use Anthropic Claude SDK directly with Wflo.

## What is Anthropic Claude?

Claude is Anthropic's AI assistant, known for:
- Long context windows (200K tokens)
- Strong reasoning capabilities
- Excellent at following complex instructions
- Tool use (function calling)

## Popular Claude Use Cases

- **Document analysis**: Process long PDFs, contracts
- **Code review**: Analyze entire codebases
- **Research**: Deep analysis with long context
- **Content moderation**: Safe, nuanced decisions

## What Wflo Adds

| Vanilla Claude | With Wflo |
|----------------|-----------|
| Manual cost tracking | ✅ Automatic tracking |
| No budget limits | ✅ Budget enforcement |
| Basic retries | ✅ Smart retry with backoff |
| Limited monitoring | ✅ Full observability |
| No state management | ✅ Checkpointing |

## Examples

- `basic_claude.py` - Simple Claude chat WITHOUT wflo
- `wflo_wrapped_claude.py` - Same with wflo integration
- `long_context_analysis.py` - Process 100K token documents
- `claude_tool_use.py` - Tool use with cost limits
