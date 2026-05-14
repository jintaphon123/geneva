# Agent Patterns Deep-Dive

## Pattern Decision Tree

```
Can a single well-structured prompt solve this?
  YES → Don't build an agent system
  NO  ↓

Are the steps sequential with dependencies?
  YES → Sequential / Supervisor pattern
  NO  → Parallel pattern

Does each step need a different expertise/persona?
  YES → Supervisor with specialists
  NO  → Sequential with one agent

Is quality verification needed before output?
  YES → Add Evaluator phase at the end
```

## Sequential Pattern
```python
# Steps must complete in order — each output feeds the next
async def sequential_pipeline(input_data):
    step1_result = await researcher(input_data)
    step2_result = await analyzer(step1_result)
    step3_result = await writer(step2_result)
    return step3_result
```
**Use when:** Research → Analysis → Synthesis flows. Phase N depends on Phase N-1.

## Parallel Pattern
```python
# Independent subtasks — aggregate at the end
async def parallel_analysis(query):
    results = await asyncio.gather(
        search_web(query),
        search_database(query),
        search_knowledge_base(query)
    )
    return synthesizer(results)
```
**Use when:** Multiple independent sources, parallel validation, competitive analysis.

## Supervisor Pattern
```python
# Orchestrator delegates to specialists
async def supervisor(task):
    plan = await coordinator.plan(task)
    results = []
    for subtask in plan.subtasks:
        specialist = route_to_specialist(subtask.type)
        result = await specialist.execute(subtask)
        results.append(result)
    return coordinator.synthesize(results)
```
**Use when:** Complex tasks requiring different expertise per subtask.

## Evaluator Pattern (quality gate)
```python
# Generator → Quality Judge → loop if failing
async def with_quality_gate(task, max_loops=2):
    for attempt in range(max_loops):
        output = await generator(task)
        score = await evaluator(output, task)
        if score.passes:
            return output
        task = task.with_feedback(score.feedback)
    return output  # deliver with warning after max loops
```
**Use when:** Output quality is critical and verifiable. Research, analysis, content.

## Agent Role Definition Template
```yaml
agent:
  name: [descriptive-name]
  purpose: "[One sentence: what problem it solves]"
  inputs:
    - name: [field]
      type: [string|array|object]
      description: [what this field contains]
  outputs:
    - name: [field]
      type: [type]
      description: [what this field contains]
  tools: [list of tool names]
  constraints:
    - "[Hard rule 1]"
    - "[Hard rule 2]"
  handoff:
    to: [next-agent-name]
    on_failure: retry|escalate|abort
```

## Common Agent Archetypes

**Coordinator** — orchestrates, never executes domain work directly  
**Specialist** — deep in one domain, refuses out-of-scope tasks  
**Researcher** — reads and synthesizes, never writes or decides  
**Critic** — finds flaws, never suggests solutions (avoid bias)  
**Synthesizer** — combines multiple inputs into a coherent output  

## Memory Patterns for Second Brain
```
Short-term (in-context):
  → current task state + active conversation
  → cleared between sessions

Long-term (file-based):
  → .md files in context/ and projects/
  → indexed in vector DB (if implemented)
  → retrieved by semantic search

Shared state (between agents in same session):
  → single source-of-truth file (decisions/log.md)
  → append-only to avoid conflicts
```
