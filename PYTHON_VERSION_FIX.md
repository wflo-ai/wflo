# Python 3.13 Compatibility Fix

## Issue

`asyncpg` version 0.29.0 (required dependency) doesn't support Python 3.13 yet due to breaking changes in Python's C API.

## Solution

Use Python 3.11 or 3.12. The project now specifies: `python = ">=3.11,<3.13"`

## Steps for Your Local Machine

### Option 1: Use Python 3.11 (Recommended)

```bash
# Check if you have Python 3.11
python3.11 --version

# If you have Python 3.11, tell Poetry to use it
poetry env use python3.11

# Remove existing environment if needed
poetry env remove python

# Create new environment with Python 3.11
poetry env use python3.11

# Install dependencies
poetry install

# Verify installation
poetry run python --version
# Should output: Python 3.11.x
```

### Option 2: Use Python 3.12

```bash
# Check if you have Python 3.12
python3.12 --version

# Tell Poetry to use Python 3.12
poetry env use python3.12

# Install dependencies
poetry install

# Verify installation
poetry run python --version
# Should output: Python 3.12.x
```

### Option 3: Install Python 3.11 (if you don't have it)

**macOS (using Homebrew):**
```bash
brew install python@3.11
poetry env use python3.11
poetry install
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
poetry env use python3.11
poetry install
```

**Windows:**
1. Download Python 3.11 from https://www.python.org/downloads/
2. Install it
3. Run: `poetry env use python3.11`
4. Run: `poetry install`

## Verification

After installation, verify all modules work:

```bash
poetry run python -c "
from wflo.cost import CostTracker, TokenUsage
from wflo.observability import get_logger
from wflo.cache import DistributedLock, LLMCache
from wflo.events import KafkaProducer, WorkflowEvent
print('✅ All modules imported successfully!')
"
```

Expected output:
```
✅ All modules imported successfully!
```

## Test Cost Calculation

```bash
poetry run python -c "
from wflo.cost import CostTracker, TokenUsage

tracker = CostTracker()
usage = TokenUsage(model='gpt-4-turbo', prompt_tokens=1000, completion_tokens=500)
cost = tracker.calculate_cost(usage)
print(f'GPT-4 Turbo: \${cost:.5f}')

usage = TokenUsage(model='claude-3-5-sonnet-20241022', prompt_tokens=1000, completion_tokens=500)
cost = tracker.calculate_cost(usage)
print(f'Claude 3.5 Sonnet: \${cost:.5f}')
"
```

Expected output:
```
GPT-4 Turbo: $0.02500
Claude 3.5 Sonnet: $0.01050
```

## Troubleshooting

### Error: "asyncpg" build failed

**Cause:** You're using Python 3.13

**Solution:** Switch to Python 3.11 or 3.12 (see above)

### Error: "python3.11: command not found"

**Solution:** Install Python 3.11 using the instructions above

### Error: "No module named 'wflo'"

**Solution:**
```bash
# Reinstall the project
poetry install
```

### Error: Import errors for modules

**Solution:**
```bash
# Clear cache and reinstall
poetry cache clear pypi --all
poetry env remove python
poetry env use python3.11
poetry install
```

## Why Python 3.13 Doesn't Work

Python 3.13 introduced breaking changes to the C API:
- `_PyLong_AsByteArray` now requires 6 arguments instead of 5
- `_PyInterpreterState_GetConfig` was removed
- `_PyUnicode_FastCopyCharacters` is no longer available

asyncpg uses Cython and compiles C extensions that rely on these APIs. The asyncpg team is working on Python 3.13 support, but it's not ready yet.

## When Will Python 3.13 Be Supported?

Track progress here: https://github.com/MagicStack/asyncpg/issues

Once asyncpg releases a Python 3.13 compatible version, we'll update the project to support it.

## Next Steps

After fixing Python version:

1. **Install dependencies:** `poetry install`
2. **Verify modules:** Run verification script above
3. **Start Docker services:** `docker-compose up -d`
4. **Run tests:** `./scripts/run_tests.sh integration`

See **GETTING_STARTED.md** for complete setup instructions.
