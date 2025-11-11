# CrewAI Integration with Wflo

This example shows how to use CrewAI with Wflo for production-ready multi-agent systems.

## What is CrewAI?

CrewAI is a role-based multi-agent framework where AI agents work together as a "crew" to accomplish tasks.

**Stats**: 30.5K GitHub stars, 1M monthly downloads

## Key Features CrewAI Provides

- **Role-based agents**: Each agent has specific role and goal
- **Task delegation**: Agents collaborate and delegate
- **Sequential/Parallel execution**: Flexible task ordering
- **Built-in tools**: 100+ pre-built tool integrations

## What Wflo Adds on Top

| CrewAI Feature | Wflo Enhancement |
|----------------|------------------|
| Multi-agent teams | ✅ Per-agent cost tracking |
| Task execution | ✅ Budget limits per agent/crew |
| Collaboration | ✅ Consensus voting for decisions |
| Error handling | ✅ Circuit breakers per agent |
| Task delegation | ✅ Approval gates for high-cost tasks |

## Use Cases

1. **Content Marketing Team**: Writer + Editor + SEO Specialist
2. **Code Review Crew**: Analyzer + Security Expert + Reviewer
3. **Customer Support**: Triage + Resolver + Escalation
4. **Research Team**: Planner + Searcher + Analyst + Writer

## Examples

- `basic_crew.py` - Simple CrewAI workflow WITHOUT wflo
- `wflo_wrapped_crew.py` - Same workflow WITH wflo integration
- `content_team.py` - Production example with budget per agent
- `code_review_crew.py` - Multi-agent code review with approvals
