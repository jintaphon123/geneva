---
name: llm-engineer
description: LLM engineering covering prompt writing, cost optimization, model routing, prompt versioning, quality evaluation, and production AI feature design. Auto-invoke when Bond asks to write or improve a prompt, reduce LLM API costs, choose between LLM models, design AI features, build prompt templates, evaluate LLM output quality, set up prompt versioning, or audit token usage. Trigger phrases: "optimize this prompt", "which model should I use", "my AI costs are too high", "write a prompt for", "few-shot examples", "structured output", "chain of thought", "prompt caching", "prompt registry", "eval pipeline", "token usage", "LLM quality", "is this prompt good", "make this prompt cheaper", "model routing", "production AI feature".
---

# LLM Engineer

Prompt writing, cost optimization, model routing, versioning, and quality evaluation. Three modes: **write** (craft prompts), **cost** (reduce spend), **govern** (manage prompts in production).

---

## Mode 1 — Write

### Prompt Patterns

| Pattern | When To Use | Token Cost |
|---------|-------------|-----------|
| **Zero-shot** | Simple, well-defined task | Low |
| **Few-shot** | Complex tasks needing consistent format | Med |
| **Chain-of-Thought** | Reasoning, math, multi-step logic | High |
| **Role** | Need specific expertise or perspective | Low |
| **Structured Output** | Need parseable JSON/XML response | Low |
| **HyDE** | Query style ≠ document style (RAG) | Med |

### Prompt Writing Framework

Every good prompt has 4 elements:

```
1. ROLE      "You are [role with specific expertise]..."
2. CONTEXT   Background info the model needs to do the task
3. TASK      Precise instruction (use active verbs: extract, classify, summarize)
4. FORMAT    Exact output shape (JSON schema, numbered list, max 3 sentences)
```

**Example — weak to strong:**
```
Weak: "Please carefully analyze the following text and provide a comprehensive summary"
Strong: "Summarize in 2 sentences. Focus on: (1) main decision, (2) deadline."

Weak: "Analyze the user's intent"  
Strong: "Classify the user's intent as one of: [buy, research, support, complaint]. Respond with JSON: {intent, confidence_0_to_1}"
```

### Few-Shot Design

3-5 examples, not 10. Cover: simple case + edge case + failure case.

```
Example 1 (simple):
Input: "Love my new iPhone 15, camera is amazing!"
Output: {"product": "iPhone 15", "sentiment": "positive", "aspect": "camera"}

Example 2 (mixed):
Input: "Laptop is okay but battery life is terrible"
Output: {"product": "laptop", "sentiment": "mixed", "aspect": "battery life"}

Example 3 (edge — no product):
Input: "This is the worst service I've ever experienced"
Output: {"product": null, "sentiment": "negative", "aspect": "service"}
```

### Structured Output

```python
# Claude — use tool_use or specify schema in prompt
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=[{
        "name": "extract_data",
        "description": "Extract structured data",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "maxLength": 200},
                "sentiment": {"enum": ["positive", "negative", "neutral"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["summary", "sentiment"]
        }
    }],
    messages=[{"role": "user", "content": f"Extract data from: {text}"}]
)

# Fallback — prompt-enforced JSON
"""Respond ONLY with valid JSON. No markdown. No explanation.
Schema: {"summary": string, "sentiment": "positive"|"negative"|"neutral"}
Start with { end with }"""
```

### Output Length Control

```python
# Always set max_tokens per endpoint — never global default
endpoint_configs = {
    "classification": {"max_tokens": 20},    # just the label
    "summary": {"max_tokens": 150},          # 2-3 sentences
    "code_review": {"max_tokens": 800},      # detailed feedback
    "chat": {"max_tokens": 400},             # conversational
}

# Explicit instructions beat max_tokens for quality
"Respond in 1-2 sentences. Be direct."
"List exactly 3 items. No explanation."
```

---

## Mode 2 — Cost

### Model Routing (60-80% cost reduction)

Route by task complexity — never default to the large model.

| Task Type | Right Model | Example |
|-----------|-------------|---------|
| Classification, extraction, yes/no | Small (Haiku 4.5) | "Is this spam?" |
| Summarization, structured output | Mid (Sonnet 4.6) | "Summarize this ticket" |
| Complex reasoning, code gen, long context | Large (Opus 4.7) | "Architect this system" |

```python
def route_to_model(task_type: str, input_tokens: int) -> str:
    if task_type in ["classify", "extract", "yes_no"] and input_tokens < 2000:
        return "claude-haiku-4-5"
    elif task_type in ["summarize", "structured_output", "rewrite"]:
        return "claude-sonnet-4-6"
    else:
        return "claude-opus-4-7"
```

### Prompt Caching (40-90% cost reduction on cached content)

```python
# Anthropic — cache_control on static content
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": LARGE_SYSTEM_PROMPT,  # 2000+ tokens
            "cache_control": {"type": "ephemeral"}  # cache for 5 min
        }
    ],
    messages=[{"role": "user", "content": user_query}]
)

# Cache-eligible (static across requests):
# - System prompts
# - Document context
# - Few-shot examples
# - Tool definitions

# NOT cache-eligible (dynamic per request):
# - User input
# - Session state
# - Timestamps
```

**Target hit rates:**
- Document Q&A: >60%
- Chatbot with static system prompt: >40%

### Cost Audit Checklist

```
RED FLAGS — fix immediately:
□ No per-feature cost breakdown
□ All requests hitting same model (model monoculture)
□ System prompt >2,000 tokens, no caching
□ max_tokens not set per endpoint
□ No cost alerts configured

QUICK WINS:
□ Route 20% of simple requests to Haiku → immediate savings
□ Cache system prompt → biggest single win on chatbots
□ Set max_tokens per endpoint → eliminate over-generation
□ Add "Respond in X sentences" to verbose prompts
```

### Token Compression

```
COMPRESS:
"Please carefully analyze the following text and provide..."  → "Analyze:"
"It is important that you remember to always..."             → "Always:"
Repeated context already in system prompt                    → Remove
HTML/markdown when plain text works                          → Strip

DON'T COMPRESS:
Task-critical instructions (hallucination risk)
Schema definitions
Constraint boundaries
Security rules
```

### Cost-Efficient Architecture

```
User Request
    ↓
Complexity Classifier (small model or rules)
    ↓
Model Router → Haiku (simple) / Sonnet (medium) / Opus (complex)
    ↓
Cache Layer → Semantic cache (Redis + embeddings) → LLM API
    ↓
Response

Budget controls:
- Per feature: hard limit + 80% soft alert
- Per user tier: free → Haiku only; paid → Sonnet; premium → Opus
- Graceful degradation: over budget → smaller model → cached response → queue
```

---

## Mode 3 — Govern

### Prompt Registry (File-Based)

```
prompts/
  registry.yaml
  memory-indexer/
    v1.0.0.md
    v1.1.0.md   ← production
  context-retriever/
    v2.3.0.md
```

```yaml
# registry.yaml
prompts:
  - id: memory-indexer
    owner: bond
    model: claude-sonnet-4-6
    versions:
      - version: 1.1.0
        file: memory-indexer/v1.1.0.md
        status: production
        promoted_at: 2026-05-01
```

**Rule:** Prompts hardcoded in source code = prompt changes require code deploys. Move to registry immediately.

### Eval Pipeline

Every production prompt needs a golden dataset: ≥20 examples, covering edge cases, reviewed by domain expert.

```python
# Eval types by task
task_eval_map = {
    "classification": "exact_match",      # target: >95% accuracy
    "extraction": "exact_match",          # target: >95%
    "summarization": "llm_judge",         # target: >0.85 score
    "structured_output": "schema_valid",  # target: 100%
    "generation": "human_eval",           # target: >80% approval
}

def run_eval(prompt_version, golden_dataset):
    results = []
    for example in golden_dataset:
        output = call_llm(prompt_version, example["input"])
        score = evaluate(output, example["expected"], task_eval_map[example["type"]])
        results.append({"input": example["input"], "score": score})
    
    pass_rate = sum(r["score"] >= threshold for r in results) / len(results)
    return {"pass_rate": pass_rate, "results": results}
```

### Deployment Lifecycle

```
DEVELOP → EVAL (automated CI) → COMPARE vs production → REVIEW (PR) → PROMOTE → MONITOR (24-48h) → ROLLBACK if needed
```

**A/B test requirements:**
- Define success metric BEFORE starting
- Min 1 week or 1,000 requests per variant
- Check for novelty effect (day-1 spike)
- p<0.05 statistical significance before declaring winner
- Monitor cost + latency alongside quality

---

## Quality Self-Evaluation

After writing any prompt or building any AI feature, score it:

| Axis | What to check | Score |
|------|--------------|-------|
| **Correctness** | Does it do what was asked? Any edge cases broken? | /10 |
| **Efficiency** | Token count justified? Could it be 30% shorter? | /10 |
| **Robustness** | What happens with adversarial input? Empty input? | /10 |
| **Maintainability** | Is it versioned? Can someone else modify it? | /10 |

Score <7 on any axis = don't ship. Fix first.

---

## Proactive Flags

Surface these without being asked:

- **Prompts hardcoded in source code** → extract to registry
- **No cost breakdown by feature** → instrument before any optimization
- **System prompt >2,000 tokens with no caching** → high-value cache target
- **max_tokens not set per endpoint** → active cost leak
- **No eval golden dataset** → you're deploying blind
- **All requests hitting one model** → model monoculture, fix with routing

---

## Quick Reference

### Model Pricing (approximate, verify with provider)
| Model | Input | Output | Best For |
|-------|-------|--------|---------|
| claude-haiku-4-5 | ~$0.25/1M | ~$1.25/1M | Classification, simple extraction |
| claude-sonnet-4-6 | ~$3/1M | ~$15/1M | Most production workloads |
| claude-opus-4-7 | ~$15/1M | ~$75/1M | Complex reasoning, agentic tasks |

### Prompt Compression Ratio Targets
- System prompt: aim for <1,500 tokens (cache sweet spot)
- User message: <500 tokens for most tasks
- Few-shot examples: 3-5 max, not 10

---

## References

- [Prompt patterns deep-dive](references/prompt-patterns.md)
- [Cost optimization playbook](references/cost-optimization.md)
