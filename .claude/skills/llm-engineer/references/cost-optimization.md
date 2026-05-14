# LLM Cost Optimization Playbook

## Measure First, Optimize Second

**If no per-feature cost breakdown exists → instrument logging before any other change.**

```python
# Minimum logging schema per LLM request
{
    "timestamp": "ISO8601",
    "feature": "chat|search|summarize|classify",
    "model": "claude-sonnet-4-6",
    "input_tokens": 847,
    "output_tokens": 123,
    "cost_usd": 0.0038,
    "latency_ms": 1240,
    "user_tier": "free|paid|premium",
    "cache_hit": false
}
```

## Priority Order (apply in this sequence)

### 1. Model Routing (60-80% reduction on routed traffic)
```python
TASK_ROUTING = {
    # Simple tasks → Haiku
    "classify": "claude-haiku-4-5",
    "extract": "claude-haiku-4-5",
    "yes_no": "claude-haiku-4-5",
    "format": "claude-haiku-4-5",

    # Medium tasks → Sonnet
    "summarize": "claude-sonnet-4-6",
    "translate": "claude-sonnet-4-6",
    "structured_output": "claude-sonnet-4-6",
    "code_completion": "claude-sonnet-4-6",

    # Complex tasks → Opus
    "architecture": "claude-opus-4-7",
    "complex_reasoning": "claude-opus-4-7",
    "code_generation": "claude-opus-4-7",
    "agentic": "claude-opus-4-7",
}
```

### 2. Prompt Caching (40-90% reduction on cacheable traffic)
```python
# Anthropic cache_control — static sections
messages = client.messages.create(
    system=[{
        "type": "text",
        "text": SYSTEM_PROMPT,  # > 1024 tokens to be cache-eligible
        "cache_control": {"type": "ephemeral"}
    }],
    messages=[{"role": "user", "content": dynamic_user_input}]
)

# Check cache performance
print(f"Cache hit: {response.usage.cache_read_input_tokens > 0}")
print(f"Cache write: {response.usage.cache_creation_input_tokens}")
```

**Target hit rates:** Document Q&A > 60% | Chatbot with static system > 40%

### 3. Output Length Control (20-40% reduction)
```python
# Per-endpoint max_tokens — never global
ENDPOINT_LIMITS = {
    "classify": 20,       # just the label
    "summarize": 150,     # 2-3 sentences
    "chat": 400,          # conversational
    "code_review": 800,   # detailed feedback
    "code_gen": 2000,     # implementation
}

# Explicit instructions in prompt (more reliable than just max_tokens)
"Respond in exactly 1 sentence."
"List 3 items. No explanation."
```

### 4. Prompt Compression (15-30% input token reduction)
```
STRIP: "Please carefully analyze..." → "Analyze:"
STRIP: "It is important that you..." → state the rule directly
STRIP: Context already in system prompt, repeated in user message
STRIP: HTML/markdown when plain text works
KEEP:  Task-critical instructions (over-compression causes hallucinations)
KEEP:  Schema definitions
KEEP:  Constraint boundaries
```

### 5. Semantic Caching (30-60% hit rate on repeated queries)
```python
import redis
import numpy as np

class SemanticCache:
    def __init__(self, threshold=0.95):
        self.threshold = threshold
        self.r = redis.Redis()
    
    def get(self, query: str, embedding: list):
        # Check against stored embeddings
        for key in self.r.scan_iter("cache:*"):
            stored = json.loads(self.r.get(key))
            similarity = cosine_similarity(embedding, stored["embedding"])
            if similarity >= self.threshold:
                return stored["response"]
        return None
    
    def set(self, query: str, embedding: list, response: str, ttl=3600):
        key = f"cache:{hash(query)}"
        self.r.setex(key, ttl, json.dumps({"embedding": embedding, "response": response}))
```

## Red Flags (fix immediately)

| Signal | Impact | Fix |
|---|---|---|
| No per-feature cost breakdown | Can't optimize what you can't see | Add logging first |
| All requests hitting same model | Model monoculture = biggest overspend | Implement routing |
| System prompt > 2000 tokens, no caching | Multiplied cost every request | Add `cache_control` |
| `max_tokens` not set per endpoint | Active cost leak | Set per-endpoint limits |
| Free users = same model as paid | Tier mismatch | Route free → Haiku |
| No cost alerts | Spikes undetected for days | Set p95 cost-per-request alerts |

## Budget Architecture

```python
# Per-user tier model assignment
USER_TIER_MODELS = {
    "free": "claude-haiku-4-5",
    "paid": "claude-sonnet-4-6",
    "premium": "claude-opus-4-7",
}

# Graceful degradation when budget exceeded
def get_model(user_tier: str, budget_remaining: float) -> str:
    if budget_remaining <= 0:
        return "claude-haiku-4-5"  # always has budget
    return USER_TIER_MODELS[user_tier]
```
