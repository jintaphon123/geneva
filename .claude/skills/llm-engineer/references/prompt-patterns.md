# Prompt Patterns

## Pattern Catalog

### Zero-Shot
```
You are [role with specific expertise].

[Task instruction — direct, active verb]

[Context if needed]

Format: [exact output shape]
```
**Best for:** Classification, extraction, simple generation where the task is unambiguous.

### Few-Shot
```
[Task description]

Examples:
Input: [example 1]
Output: [expected 1]

Input: [example 2]
Output: [expected 2]

Input: [example 3]  ← cover edge case
Output: [expected 3]

Now process:
Input: [actual input]
Output:
```
**Best for:** Tasks with non-obvious output format, complex classification, style mimicking.
**Rule:** 3-5 examples, always include at least one edge case.

### Chain-of-Thought
```
[Task instruction]

Think step by step:
1. First, [what to analyze]
2. Then, [what to derive]
3. Finally, [what to output]

[Input]
```
**Best for:** Multi-step reasoning, math, logic problems, analysis tasks.

### Structured Output (JSON)
```
Extract the following from the text and return as JSON:
{
  "field1": "string description",
  "field2": "enum: value1|value2|value3",
  "field3": "number 0-100"
}

Rules:
- Respond ONLY with valid JSON. No markdown. No explanation.
- Start with { and end with }
- If a field cannot be determined, use null

Text: [input]
```

### Role + Persona
```
You are [specific expert with specific traits].
[2-3 sentences about what makes this persona distinctive — not generic]

[Task]

Constraints:
- [Hard rule 1]
- [Hard rule 2]
```
**Key:** The persona description must be specific, not generic ("senior engineer" → "senior engineer who has shipped 3 production systems and is allergic to unnecessary abstraction").

## Prompt Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
|---|---|---|
| "Please carefully analyze..." | Filler — model ignores it | "Analyze:" |
| "It is important that you..." | Weak framing | State the rule directly |
| "Try to..." | Introduces uncertainty | State the requirement directly |
| "Can you..." | Makes it optional | Imperative instruction |
| Asking for multiple things at once | Model will prioritize one | One clear primary task |
| No output format specified | Model chooses arbitrarily | Always specify format |

## Output Length Control
```python
# In the prompt
"Respond in exactly 3 bullet points."
"Summarize in 2 sentences. No more."
"List exactly 5 items. No explanation."

# In the API call
response = client.messages.create(
    max_tokens=150,  # always set per endpoint
    ...
)
```

## Claude-Specific Features

### Prompt Caching
```python
# Static content → cache with cache_control
system=[{
    "type": "text",
    "text": LARGE_SYSTEM_PROMPT,
    "cache_control": {"type": "ephemeral"}  # 5-min TTL
}]
```
Cache-eligible: system prompts, static docs, few-shot examples, tool definitions.

### Tool Use (structured output, more reliable than JSON prompting)
```python
tools=[{
    "name": "extract_data",
    "description": "Extract structured information",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "sentiment": {"enum": ["positive", "negative", "neutral"]}
        },
        "required": ["name", "sentiment"]
    }
}]
```

### Extended Thinking (complex reasoning)
```python
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[{"role": "user", "content": complex_problem}]
)
```
Use for: multi-step math, complex code architecture, ambiguous trade-off analysis.
