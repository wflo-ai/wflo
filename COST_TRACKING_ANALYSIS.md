# Cost Tracking Implementation Analysis

## Current State

### What We Have

**1. Custom Implementation (`src/wflo/cost/tracker.py`)**
- Manual pricing table with 20+ models (GPT-4, GPT-3.5, Claude, Llama, Mistral)
- Token counting using `tiktoken` library
- `CostTracker` class with methods:
  - `calculate_cost(usage)` - Calculate cost from token usage
  - `track_cost(session, execution_id, usage)` - Save cost to database
  - `estimate_cost(model, prompt, max_tokens)` - Estimate before execution
  - `count_tokens(text, model)` - Count tokens in text
- `TokenUsage` dataclass for tracking prompt/completion tokens
- `check_budget()` function for budget enforcement

**2. Temporal Activities (`src/wflo/temporal/activities.py`)**
- `track_cost()` activity - Updates workflow execution and step execution costs in database
- `check_budget()` activity - Checks if workflow is within budget limits
- Direct database updates (similar to CostTracker.track_cost)

**3. Database Models (`src/wflo/db/models.py`)**
- `WorkflowExecutionModel`: cost_total_usd, cost_prompt_tokens, cost_completion_tokens
- `StepExecutionModel`: cost_usd, prompt_tokens, completion_tokens

### Dependencies Available

- ✅ `tokencost ^0.1.0` - Already in pyproject.toml but NOT being used
- ✅ `tiktoken ^0.6.0` - Currently used for token counting

## Problems Identified

### 1. **Not Using tokencost Library**
We have `tokencost` in dependencies but implemented everything manually:
- **Manual pricing table** (20+ models) vs tokencost's 400+ models with auto-updates
- **Manual model normalization** vs tokencost's built-in model name handling
- **Manual encoding selection** vs tokencost's automatic tokenizer selection

### 2. **Code Duplication**
- `CostTracker.track_cost()` and `track_cost()` activity do similar database updates
- `check_budget()` function exists in both `cost/tracker.py` and `temporal/activities.py`

### 3. **Maintenance Burden**
- Pricing table needs manual updates when providers change prices
- Model support requires manual addition of each new model
- Encoding logic duplicates what tokencost already does

### 4. **Limited Model Support**
- Our manual table: ~20 models
- tokencost library: 400+ models (OpenAI, Anthropic, Azure, Mistral, Cohere, etc.)
- Missing support for: Azure OpenAI variants, Cohere, newer Claude versions, etc.

## tokencost Library Analysis

### API Overview

```python
from tokencost import calculate_prompt_cost, calculate_completion_cost

# Calculate costs directly
prompt_cost = calculate_prompt_cost(prompt, model="gpt-4")
completion_cost = calculate_completion_cost(completion, model="gpt-4")

# Count tokens
from tokencost import count_message_tokens, count_string_tokens
tokens = count_string_tokens("Hello world", model="gpt-4")
```

### Key Features

1. **400+ LLM Support**: OpenAI, Anthropic, Azure, Mistral, Cohere, Google, Meta, etc.
2. **Auto-Updated Pricing**: Library maintainers keep pricing current
3. **Built-in Tokenization**: Uses tiktoken for OpenAI, Anthropic API for Claude 3+
4. **Simple API**: Single function calls for cost calculation
5. **Model Name Handling**: Automatically normalizes model names
6. **ChatML Support**: Handles message formats with proper token counting

### Advantages Over Our Implementation

| Feature | Our Implementation | tokencost |
|---------|-------------------|-----------|
| Model support | 20 models | 400+ models |
| Pricing updates | Manual | Auto-updated |
| Code complexity | ~330 lines | Single function calls |
| Tokenization | Manual encoding selection | Automatic |
| Message format | Only strings | ChatML + strings |
| Maintenance | We maintain | Community maintains |

## Recommended Improvements

### Phase 1: Refactor to Use tokencost

**Goal**: Simplify implementation by leveraging tokencost library

**Changes**:
1. Replace `CostTracker.calculate_cost()` with `tokencost.calculate_prompt_cost()` + `calculate_completion_cost()`
2. Replace `CostTracker.count_tokens()` with `tokencost.count_string_tokens()`
3. Remove manual MODEL_PRICING table
4. Remove manual encoding selection logic
5. Keep database tracking logic (track_cost, check_budget)

**Benefits**:
- ✅ Reduce code from ~330 lines to ~150 lines
- ✅ Support 400+ models automatically
- ✅ Get automatic pricing updates
- ✅ Simplify maintenance

**Example Refactored Code**:
```python
from tokencost import calculate_prompt_cost, calculate_completion_cost, count_string_tokens

class CostTracker:
    """Simplified cost tracker using tokencost library."""

    def calculate_cost(self, usage: TokenUsage) -> float:
        """Calculate cost using tokencost library."""
        # tokencost uses tokens directly
        prompt_cost = (usage.prompt_tokens / 1_000_000) * get_prompt_price_per_million(usage.model)
        completion_cost = (usage.completion_tokens / 1_000_000) * get_completion_price_per_million(usage.model)
        return prompt_cost + completion_cost

    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens using tokencost."""
        return count_string_tokens(text, model)

    def estimate_cost(self, model: str, prompt: str, max_completion_tokens: int = 500) -> float:
        """Estimate cost using tokencost."""
        prompt_cost = calculate_prompt_cost(prompt, model)
        # Estimate completion cost based on max tokens
        completion_cost = (max_completion_tokens / 1_000_000) * get_completion_price_per_million(model)
        return prompt_cost + completion_cost
```

### Phase 2: Consolidate Database Tracking

**Goal**: Eliminate duplication between CostTracker and Temporal activities

**Changes**:
1. Make Temporal activities use CostTracker methods
2. Remove duplicate database logic from activities
3. Centralize all cost tracking in CostTracker class

**Example**:
```python
# In temporal/activities.py
from wflo.cost import CostTracker, TokenUsage

@activity.defn
async def track_cost(
    execution_id: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    step_execution_id: str | None = None,
) -> None:
    """Track cost using CostTracker."""
    async for session in get_session():
        tracker = CostTracker()
        usage = TokenUsage(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        await tracker.track_cost(session, execution_id, usage, step_execution_id)
```

### Phase 3: Enhanced Cost Features

**Optional enhancements after refactoring**:

1. **Cost Breakdown by Model**
   - Track which models are used most
   - Cost attribution per model type

2. **Cost Alerts**
   - Emit events when cost thresholds reached
   - Integration with observability stack

3. **Cost Optimization Suggestions**
   - Suggest cheaper model alternatives
   - Identify expensive workflows

4. **Batch Cost Calculation**
   - Calculate costs for multiple calls at once
   - Optimize database updates

## Implementation Plan

### Step 1: Research tokencost API (✅ Complete)
- Understand function signatures
- Test with sample data
- Verify model support

### Step 2: Refactor CostTracker Class
- Replace manual pricing with tokencost calls
- Update tests to verify equivalence
- Maintain backward compatibility

### Step 3: Update Temporal Activities
- Use CostTracker in activities
- Remove duplicate logic
- Update integration tests

### Step 4: Update Documentation
- Document tokencost usage
- Update cost tracking guide
- Add model support documentation

### Step 5: Test & Validate
- Run all integration tests
- Verify cost calculations match
- Test with multiple models

## Testing Strategy

### Unit Tests
- Test CostTracker with various models
- Verify cost calculations match tokencost
- Test error handling for unknown models

### Integration Tests
- Test database tracking with real models
- Test budget checking
- Test workflow cost accumulation

### Validation Tests
- Compare old vs new cost calculations
- Verify no regression in accuracy
- Test with edge cases (new models, variants)

## Migration Considerations

### Breaking Changes
- None - API remains the same
- Only internal implementation changes

### Performance Impact
- Minimal - tokencost is lightweight
- May be slightly faster (less manual logic)

### Deployment
- No database migrations needed
- No configuration changes required
- Drop-in replacement

## Conclusion

### Summary
We currently have a well-structured but manually-maintained cost tracking system. By refactoring to use the `tokencost` library, we can:
- **Reduce code complexity** by ~50%
- **Support 400+ models** instead of 20
- **Get automatic pricing updates** without maintenance
- **Simplify tokenization logic**
- **Focus on our core features** instead of maintaining pricing tables

### Recommendation
**Proceed with Phase 1 refactoring** to leverage tokencost library. The benefits significantly outweigh the effort (estimated 2-3 hours of work).

### Next Steps
1. ✅ Complete this analysis
2. Create refactored CostTracker implementation
3. Update integration tests
4. Update Temporal activities
5. Commit and test thoroughly
