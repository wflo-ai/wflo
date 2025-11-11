# Quick Start - Simple LLM Agent Example

Get the example running in **5 minutes**!

## Prerequisites

1. **Python 3.11+** installed
2. **OpenAI API key** - Get from https://platform.openai.com/api-keys
3. **Poetry** installed (or use pip)

## Step 1: Install Dependencies

### Option A: Using Poetry (Recommended)

```bash
# From project root
poetry install
```

### Option B: Using pip

```bash
# From project root
pip install openai click
pip install -e .
```

## Step 2: Set Your API Key

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

## Step 3: Run the Example

```bash
# Simple example
python examples/simple_llm_agent/run.py --prompt "What is 2+2?"

# With custom budget
python examples/simple_llm_agent/run.py --prompt "Explain quantum computing" --budget 0.50

# With different model
python examples/simple_llm_agent/run.py --prompt "Write a haiku" --model gpt-3.5-turbo

# With system prompt
python examples/simple_llm_agent/run.py \
  --prompt "Tell me a joke" \
  --system-prompt "You are a comedian"

# Verbose mode for debugging
python examples/simple_llm_agent/run.py --prompt "Hello" --verbose
```

## Expected Output

```
🚀 Starting Wflo Simple LLM Agent Example
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Configuration:
   Prompt: What is 2+2?
   Model: gpt-4
   Budget: $1.00

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Creating LLM step...
✓ Validating inputs...
✓ Calling gpt-4 API...
✓ Response received
✓ Cost tracked: $0.0020

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Result:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2+2 equals 4. This is a basic arithmetic operation.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Execution ID:    exec-1731297600
Status:          COMPLETED
Duration:        1.23 seconds
Cost:            $0.0020 USD
Budget Used:     0.2%
Tokens:          123 (prompt: 10, completion: 113)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Workflow completed successfully!
```

## Troubleshooting

### "ERROR: Required package 'click' not installed"

Run: `poetry install` or `pip install click openai`

### "ERROR: OPENAI_API_KEY environment variable not set"

Make sure you exported your API key:
```bash
export OPENAI_API_KEY="sk-..."
```

Check it's set:
```bash
echo $OPENAI_API_KEY
```

### "ERROR: Failed to import Wflo components"

Make sure you're running from the **project root** directory (not from examples/):

```bash
# From project root:
python examples/simple_llm_agent/run.py --prompt "Hello"

# NOT from examples directory:
cd examples  # ❌ Don't do this
python simple_llm_agent/run.py --prompt "Hello"  # ❌ Won't work
```

### "Budget exceeded" error

Increase your budget or use a cheaper model:

```bash
# Increase budget
python examples/simple_llm_agent/run.py --prompt "Long text..." --budget 5.0

# Or use cheaper model
python examples/simple_llm_agent/run.py --prompt "Long text..." --model gpt-3.5-turbo
```

### API Rate Limit

If you hit OpenAI rate limits:
1. Wait a few seconds and try again
2. Use a lower tier model (gpt-3.5-turbo)
3. Check your OpenAI account limits

## Test Without API Key

To verify the setup works without calling OpenAI:

```bash
# Run basic import test
python examples/simple_llm_agent/test_example.py
```

This tests that:
- Imports work correctly
- Step system can be instantiated
- Prompt rendering works
- No API key required!

## Command Line Options

```bash
python examples/simple_llm_agent/run.py --help
```

Available options:
- `--prompt TEXT` - Your question for the LLM (required)
- `--model TEXT` - Model to use (default: gpt-4)
- `--budget FLOAT` - Max cost in USD (default: 1.0)
- `--max-tokens INT` - Max completion tokens (default: 500)
- `--temperature FLOAT` - Sampling temperature 0-2 (default: 0.7)
- `--system-prompt TEXT` - Optional system prompt
- `--verbose` - Enable debug logging

## Cost Estimates

Approximate costs with GPT-4:
- Simple question: $0.001 - $0.005
- Short explanation: $0.005 - $0.020
- Code generation: $0.010 - $0.050
- Long response: $0.050+

With GPT-3.5-turbo (10x cheaper):
- Simple question: $0.0001 - $0.0005
- Most tasks: < $0.005

## What This Demonstrates

✅ OpenAI API integration
✅ Automatic cost tracking
✅ Budget enforcement
✅ Template-based prompts
✅ Error handling
✅ Beautiful CLI output
✅ Full Wflo step system

## Next Steps

1. **Try different prompts** - Test various use cases
2. **Review the code** - See `run.py` to understand how it works
3. **Check the full README** - See `README.md` for detailed docs
4. **Build your own** - Use this as a template for custom workflows

## Getting Help

- **Full Example Docs**: `examples/simple_llm_agent/README.md`
- **Comprehensive Assessment**: `docs/COMPREHENSIVE_ASSESSMENT.md`
- **Implementation Plan**: `docs/IMPLEMENTATION_PLAN.md`
- **Project README**: `README.md`

---

**Ready?** Just run:

```bash
export OPENAI_API_KEY="sk-..."
python examples/simple_llm_agent/run.py --prompt "What is 2+2?"
```

🚀 Enjoy!
