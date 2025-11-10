# Phase 1: Cost Tracking Refactor - Implementation Plan

**Goal**: Refactor cost tracking to use tokencost library for automatic model support and pricing updates

**Estimated Effort**: 2-3 hours
**Priority**: CRITICAL
**Status**: In Progress

---

## Current Architecture Analysis

### Files to Modify
1. `src/wflo/cost/tracker.py` (~330 lines → ~150 lines expected)
2. `tests/integration/test_cost_tracking.py` (11 tests - verify still pass)
3. `src/wflo/temporal/activities.py` (consolidate duplicate logic)

### Current Implementation Issues
1. **Manual Pricing Table**: 20 models with hardcoded prices (needs updates)
2. **Outdated Pricing**: GPT-4 pricing doesn't match 2025 rates
3. **Missing Models**: Claude Opus 4.1, Haiku 3.5, GPT-5 not supported
4. **Code Duplication**: track_cost logic exists in both CostTracker and Temporal activities
5. **Maintenance Burden**: Every new model/price change requires manual updates

---

## Implementation Strategy

### Step 1: Create tokencost Wrapper (Backward Compatible)

**Goal**: Wrap tokencost API to match our current interface

**New Approach**:
```python
# Instead of manual pricing:
prompt_cost = (usage.prompt_tokens / 1000) * pricing["prompt"]

# Use tokencost directly:
from tokencost import calculate_prompt_cost, calculate_completion_cost

# Convert tokens back to text is impossible, so we need a hybrid approach
# Keep TokenUsage dataclass but validate with tokencost pricing
```

**Challenge**: tokencost takes text input, we have token counts

**Solution**: Keep our TokenUsage dataclass, but fetch pricing from tokencost's internal price table

### Step 2: Refactor CostTracker Class

#### Keep These (No Changes)
- `TokenUsage` dataclass (with prompt_tokens, completion_tokens, model)
- `track_cost()` method signature (database tracking logic)
- `check_budget()` function

#### Replace These
- `MODEL_PRICING` dictionary → Use tokencost pricing
- `count_tokens()` method → Use `count_string_tokens()`
- `calculate_cost()` → Use tokencost pricing internally
- `_normalize_model_name()` → Keep but simplify
- Manual encoding selection → Use tokencost

#### New Implementation Pattern
```python
import tokencost
from tokencost import count_string_tokens

class CostTracker:
    """Simplified cost tracker using tokencost library."""

    def calculate_cost(self, usage: TokenUsage) -> float:
        """Calculate cost using tokencost pricing data.

        Since tokencost doesn't expose a tokens-to-cost API directly,
        we'll create temporary text of the right length to get pricing.
        """
        # Strategy: Use tokencost's internal pricing
        # Create dummy text with exact token count
        dummy_prompt = "x " * usage.prompt_tokens  # Rough approximation
        dummy_completion = "x " * usage.completion_tokens

        prompt_cost = calculate_prompt_cost(dummy_prompt, usage.model)
        completion_cost = calculate_completion_cost(dummy_completion, usage.model)

        return prompt_cost + completion_cost

    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens using tokencost."""
        return count_string_tokens(text, model)

    def estimate_cost(self, model: str, prompt: str, max_completion_tokens: int = 500) -> float:
        """Estimate cost using tokencost."""
        prompt_cost = calculate_prompt_cost(prompt, model)
        # For completion, estimate with dummy text
        dummy_completion = "x " * max_completion_tokens
        completion_cost = calculate_completion_cost(dummy_completion, model)
        return prompt_cost + completion_cost
```

**Problem with above**: tokencost pricing is per-text, not per-token count

**Better Solution**: Access tokencost's internal pricing data

```python
# Check if tokencost exposes pricing table
from tokencost import costs  # If available

# OR implement hybrid:
# 1. Use tokencost for token counting (count_string_tokens)
# 2. Calculate cost from token count using tokencost's pricing
# 3. Validate our calculations match tokencost's
```

### Step 3: Research tokencost Internal API

**Need to verify**:
- Can we access pricing table directly?
- Does tokencost provide a tokens-to-cost function?
- What's the relationship between text and tokens?

**Test locally**:
```python
import tokencost
from tokencost import calculate_prompt_cost, count_string_tokens

# Test: Does 100 tokens always cost the same?
text1 = "a " * 50  # ~100 tokens
text2 = "the " * 33  # ~100 tokens (roughly)

cost1 = calculate_prompt_cost(text1, "gpt-4")
cost2 = calculate_prompt_cost(text2, "gpt-4")

tokens1 = count_string_tokens(text1, "gpt-4")
tokens2 = count_string_tokens(text2, "gpt-4")

# If cost1/tokens1 == cost2/tokens2, then pricing is per-token
# This means we can calculate: cost = (tokens / million) * price_per_million
```

---

## Detailed Implementation Steps

### Phase 1.1: Research tokencost Internal API ✓

**Actions**:
- [x] Check tokencost source code for pricing table access
- [x] Verify token count → cost calculation method
- [ ] Test with local installation

### Phase 1.2: Create Hybrid Solution (15 min)

**Implementation**:
```python
# Option A: Use tokencost for everything (text-based)
def calculate_cost_from_text(prompt: str, completion: str, model: str) -> float:
    return calculate_prompt_cost(prompt, model) + calculate_completion_cost(completion, model)

# Option B: Hybrid - keep TokenUsage, use tokencost pricing
def calculate_cost_from_tokens(usage: TokenUsage) -> float:
    # Use tokencost's internal pricing per token
    # Calculate cost = (tokens / 1_000_000) * cost_per_million
    pass
```

**Decision**: Research tokencost source to find pricing table

### Phase 1.3: Refactor CostTracker (30 min)

**Changes**:
1. Remove `MODEL_PRICING` dictionary
2. Update `calculate_cost()` to use tokencost
3. Update `count_tokens()` to use `count_string_tokens()`
4. Simplify `estimate_cost()` to use tokencost
5. Keep database tracking logic unchanged

**Test After Each Change**:
```bash
pytest tests/integration/test_cost_tracking.py::TestCostTracker::test_calculate_cost_gpt4 -v
```

### Phase 1.4: Update Integration Tests (20 min)

**Verify**:
- All 11 tests still pass
- Cost calculations match expected values
- Token counting is accurate
- Budget checking works correctly

**Update Expected Values**:
- GPT-4 pricing may differ (update assertions)
- Add tests for new 2025 models

### Phase 1.5: Consolidate Temporal Activities (30 min)

**Current Duplication**:
```python
# In temporal/activities.py
@activity.defn
async def track_cost(...):
    # Direct database updates (duplicates CostTracker.track_cost)
    pass
```

**New Pattern**:
```python
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

### Phase 1.6: Add New 2025 Models (10 min)

**Test Support For**:
- Claude Opus 4.1 ($15/$75 per 1M)
- Claude Haiku 3.5 ($0.80/$4 per 1M)
- Claude Sonnet 4.5 ($3/$15 per 1M) ✓ Already in tests
- GPT-5 (pricing TBD)
- GPT-4o ($5/$20 per 1M)

**Add Tests**:
```python
async def test_calculate_cost_claude_opus_41(self, db_session):
    """Test cost calculation for Claude Opus 4.1 (2025 model)"""
    tracker = CostTracker()
    usage = TokenUsage(
        model="claude-opus-4.1",
        prompt_tokens=1000,
        completion_tokens=500,
    )
    cost = tracker.calculate_cost(usage)
    # Opus 4.1: $15/$75 per 1M
    expected = (1000 * 15 / 1_000_000) + (500 * 75 / 1_000_000)
    assert abs(cost - expected) < 0.0001
```

### Phase 1.7: Update Documentation (10 min)

**Files to Update**:
- `tests/integration/README.md` - Update cost tracking section
- `COST_TRACKING_ANALYSIS.md` - Mark Phase 1 as complete
- Add migration notes

### Phase 1.8: Run Full Test Suite (5 min)

```bash
# Run all cost tracking tests
pytest tests/integration/test_cost_tracking.py -v

# Run database tests (ensure no regressions)
pytest tests/integration/test_database.py -v

# Run all integration tests
pytest tests/integration/ -v --no-cov
```

### Phase 1.9: Commit and Push (5 min)

**Commit Message**:
```
feat(cost): refactor to use tokencost library for 400+ model support

Replace manual pricing table with tokencost library integration for
automatic model support and pricing updates.

Changes:
- Refactor CostTracker to use tokencost for pricing and token counting
- Consolidate Temporal activity track_cost to use CostTracker
- Remove manual MODEL_PRICING table (20 models → 400+ via tokencost)
- Add support for 2025 models (Claude Opus 4.1, Haiku 3.5, GPT-5)
- Update integration tests for new implementation
- Simplify code from ~330 to ~150 lines

Benefits:
- Automatic pricing updates from tokencost maintainers
- 400+ model support (vs our 20)
- Simplified maintenance
- Accurate 2025 pricing

Testing:
- All 11 integration tests pass
- Verified cost calculations match tokencost
- Added tests for new 2025 models
```

---

## Alternative Implementation (If Needed)

### If tokencost doesn't expose pricing table:

**Approach**: Use tokencost for validation, keep lightweight pricing cache

```python
import tokencost
from functools import lru_cache

@lru_cache(maxsize=256)
def get_model_pricing(model: str) -> dict[str, float]:
    """Get pricing by testing with tokencost."""
    # Calculate cost per token by testing
    single_token_text = "a"
    prompt_cost_per_token = calculate_prompt_cost(single_token_text, model)
    completion_cost_per_token = calculate_completion_cost(single_token_text, model)

    return {
        "prompt": prompt_cost_per_token * 1_000_000,  # Per million
        "completion": completion_cost_per_token * 1_000_000,
    }
```

---

## Success Criteria

- [ ] All 11 integration tests pass
- [ ] CostTracker uses tokencost library
- [ ] No manual pricing table
- [ ] Support for 400+ models
- [ ] Claude Opus 4.1, Haiku 3.5, GPT-5 supported
- [ ] Code reduced from ~330 to ~150 lines
- [ ] Temporal activities consolidated
- [ ] Documentation updated
- [ ] Committed and pushed

---

## Risk Mitigation

### Risk 1: tokencost API doesn't match our needs
**Mitigation**: Hybrid approach - use tokencost pricing table, keep TokenUsage

### Risk 2: Integration tests fail
**Mitigation**: Update expected values based on tokencost's pricing

### Risk 3: Performance regression
**Mitigation**: Benchmark before/after, cache pricing lookups

---

## Next Steps After Phase 1

Once Phase 1 is complete:
- Review implementation
- Merge to main
- Begin Phase 2: Observability (structlog, OpenTelemetry, Prometheus)

**Estimated Total Time**: 2-3 hours
