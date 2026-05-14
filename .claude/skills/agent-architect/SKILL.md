---
name: agent-architect
description: Multi-agent system design and RAG pipeline architecture for AI-first products. Auto-invoke when Bond asks to design an AI agent system, build a multi-agent workflow, architect a RAG pipeline, choose a vector database, design agent-to-agent handoffs, build an orchestration layer, or plan autonomous agent loops. Trigger phrases: "design a multi-agent system", "build an agent workflow", "RAG pipeline", "vector database", "agent orchestration", "how should agents communicate", "design my AI memory system", "embedding strategy", "retrieval strategy", "agent patterns", "LLM orchestration", "autonomous agents", "tool design for agents", "how to split this into agents", "context window management".
---

# Agent Architect

Design multi-agent systems and RAG pipelines. Two modes: **agents** (system architecture) and **rag** (retrieval pipeline).

---

## Mode 1 — Agents

### Pattern Selection

Pick the smallest pattern that works. Don't over-architect.

| Pattern | Use When | Avoid When |
|---------|----------|------------|
| **Single Agent** | One scope, one tool set, clear boundaries | Task requires parallel work |
| **Sequential** | Step A must complete before step B | Steps are independent |
| **Parallel** | Independent subtasks that can run concurrently | Order matters or outputs conflict |
| **Supervisor** | Central coordinator + specialist workers | Coordinator becomes bottleneck |
| **Evaluator** | Generator + quality gate loop | Simple one-shot tasks |
| **Router** | Dispatch by intent/type to specialized handlers | All inputs need same treatment |

**Decision rule:** Can a single well-structured prompt solve this? If yes, don't build an agent system.

---

### Agent Role Definition

Every agent needs all 5 fields:

```yaml
agent:
  name: memory-indexer
  purpose: "Index new .md files into the knowledge graph"
  inputs:
    - file_path: string
    - content: string
  outputs:
    - indexed_chunks: array
    - metadata: object
  tools: [read_file, write_index, embed_text]
  constraints:
    - "Only process .md files"
    - "Max 50 chunks per file"
    - "Never modify source files"
```

**Common archetypes:**
- **Coordinator** — orchestrates, allocates, monitors, escalates
- **Specialist** — deep expertise in one domain, clear handoff for out-of-scope
- **Interface** — handles external I/O, protocol translation, auth
- **Monitor** — health checks, anomaly detection, audit logging

---

### Handoff Contracts

Every edge between agents needs an explicit contract:

```typescript
interface HandoffPayload {
  task_id: string;
  from_agent: string;
  to_agent: string;
  artifacts: {          // only what the next agent needs — no full context dump
    [key: string]: unknown;
  };
  metadata: {
    timestamp: string;
    tokens_used: number;
    confidence?: number;  // include if agent has uncertainty
  };
  on_failure: 'retry' | 'escalate' | 'abort';
}
```

**Anti-pattern:** Passing full upstream context to every agent. Each agent should receive only the artifacts it needs.

---

### Context & Cost Discipline

LLM calls are the expensive step. Every agent system needs budget control:

```yaml
workflow_config:
  max_tokens_per_step: 4000
  max_total_tokens: 20000
  timeout_per_step: 30s
  max_retries: 2
  retry_backoff: exponential

  # Context trimming — before passing to next agent:
  # 1. Extract only relevant artifacts (not full conversation)
  # 2. Summarize intermediate results if token budget is tight
  # 3. Use file-based state for persistence (not in-context)
```

---

### Error Handling Patterns

```python
# Retry with exponential backoff
async def call_agent(agent, payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await agent.execute(payload)
        except TransientError as e:
            wait = 2 ** attempt + random.random()
            await asyncio.sleep(wait)
    raise PermanentFailure(f"Agent {agent.name} failed after {max_retries} attempts")

# Circuit breaker — stop hammering a failing agent
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failures = 0
        self.state = 'closed'  # closed = normal, open = stop calls
```

---

### Memory Architecture (for Second Brain context)

```
Short-term (in-context):
  → Current task state, active conversation
  → Cleared between sessions

Long-term (file-based / vector store):
  → .md files in context/ and projects/ → indexed in vector DB
  → Persists across sessions, retrieved by semantic search

Shared memory (between agents):
  → Single source of truth file (e.g., decisions/log.md)
  → Agent reads before writing; uses file lock or append-only
```

---

### Safety Guardrails

Always wire these into any production agent system:

1. **Input validation** — schema + content check before agent runs
2. **Human-in-the-loop checkpoint** — for irreversible actions (file delete, send email)
3. **Output validation** — check agent output before passing to next step
4. **Audit logging** — every tool call logged with timestamp + result
5. **Rate limiting** — cap LLM calls per minute per agent

---

## Mode 2 — RAG

### Pipeline Architecture

```
Documents → Chunking → Embedding → Vector DB → Retrieval → LLM
              ↓                         ↓
           Metadata               Query transform
```

---

### Chunking Strategy Selection

| Strategy | Best For | Token Range |
|----------|----------|-------------|
| **Sentence-based** | Articles, narrative text | 100-300 |
| **Paragraph-based** | Technical docs, structured content | 200-600 |
| **Semantic** | Long-form, research papers | variable |
| **Fixed + overlap** | Uniform docs, simple RAG | 512 + 10-20% overlap |
| **Recursive** | Mixed content types | variable |

**For Second Brain `.md` files:** Paragraph-based + 15% overlap. Respect H2/H3 boundaries as natural chunk breaks.

---

### Embedding Model Selection

| Model | Dimensions | Speed | Cost | Best For |
|-------|-----------|-------|------|---------|
| `all-MiniLM-L6-v2` | 384 | Fast | Free (local) | Dev, small corpus |
| `all-mpnet-base-v2` | 768 | Med | Free (local) | Balanced quality |
| `text-embedding-3-small` | 1536 | Fast | $0.02/1M tokens | Production, general |
| `text-embedding-3-large` | 3072 | Med | $0.13/1M tokens | High precision |

**Default recommendation:** `text-embedding-3-small` for production, `all-MiniLM-L6-v2` for local dev.

---

### Vector DB Selection

| DB | When To Use | When To Avoid |
|----|-------------|---------------|
| **Chroma** | Local dev, prototyping | Production scale |
| **pgvector** | Already on PostgreSQL, need ACID | High write throughput |
| **Qdrant** | High performance, resource constraints | Large community/integrations needed |
| **Pinecone** | Managed production, AWS ecosystem | Cost-sensitive, vendor lock-in risk |
| **Weaviate** | Multi-modal, complex metadata | Simple use cases |

**For Second Brain:** Start with `pgvector` if using PostgreSQL, or `Chroma` for local-only prototype.

---

### Retrieval Strategies

```python
# Dense retrieval (semantic similarity)
results = vector_db.query(
    query_embedding=embed(user_query),
    top_k=10,
    filter={"project": "second-brain"}
)

# Hybrid retrieval (dense + sparse) — better precision
dense_results = vector_db.semantic_search(query, top_k=20)
sparse_results = bm25_index.search(query, top_k=20)
final = reciprocal_rank_fusion(dense_results, sparse_results)[:10]

# HyDE — when query style ≠ document style
hypothesis = llm.generate(f"Write a document that answers: {query}")
results = vector_db.query(embed(hypothesis), top_k=10)
```

**Reranking** (add when precision < 0.8):
```python
from sentence_transformers import CrossEncoder
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
scores = reranker.predict([(query, chunk) for chunk in results])
reranked = sorted(zip(scores, results), reverse=True)
```

---

### Context Assembly

```python
def assemble_context(chunks, token_budget=3000):
    context = []
    used = 0
    for chunk in sorted(chunks, key=lambda c: c.score, reverse=True):
        tokens = count_tokens(chunk.text)
        if used + tokens > token_budget:
            break
        context.append(chunk)
        used += tokens
    return context

# Deduplication — remove near-duplicate chunks
def deduplicate(chunks, threshold=0.92):
    seen = []
    for chunk in chunks:
        if not any(cosine_sim(chunk.embedding, s.embedding) > threshold for s in seen):
            seen.append(chunk)
    return seen
```

---

### RAG Evaluation Metrics

| Metric | Target | What It Measures |
|--------|--------|-----------------|
| Context relevance | > 0.80 | Are retrieved chunks relevant to query? |
| Answer faithfulness | > 0.90 | Is answer grounded in retrieved context? |
| Answer relevance | > 0.85 | Does answer address the question? |
| Retrieval precision@5 | > 0.70 | How many top-5 results are relevant? |

```python
# RAGAS — comprehensive RAG evaluation
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

results = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision])
```

---

## Design Checklist

Before shipping any agent/RAG system:

- [ ] Pattern is the simplest one that works
- [ ] Every agent has defined inputs, outputs, tools, constraints
- [ ] Handoff contracts are explicit — no full context dumps
- [ ] Token budget + timeouts defined for every step
- [ ] Retry + circuit breaker wired
- [ ] Human-in-the-loop for irreversible actions
- [ ] Chunking strategy validated against actual document corpus
- [ ] Retrieval precision measured (not assumed)
- [ ] Context window budget enforced in assembly

---

## References

- [Agent patterns deep-dive](references/agent-patterns.md)
- [RAG pipeline cookbook](references/rag-cookbook.md)
