# RAG Pipeline Cookbook

## Quick Start Patterns

### Minimal RAG (local dev, prototype)
```python
# Chroma + sentence-transformers — zero cost, local only
from chromadb import Client
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
db = Client()
collection = db.create_collection("second-brain")

# Index
def index_document(text: str, doc_id: str, metadata: dict):
    embedding = model.encode(text).tolist()
    collection.add(embeddings=[embedding], documents=[text],
                   ids=[doc_id], metadatas=[metadata])

# Query
def retrieve(query: str, top_k: int = 5):
    embedding = model.encode(query).tolist()
    return collection.query(query_embeddings=[embedding], n_results=top_k)
```

### Production RAG (pgvector)
```sql
-- Postgres extension
CREATE EXTENSION vector;
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);

-- Query
SELECT content, 1 - (embedding <=> $1::vector) AS similarity
FROM documents
ORDER BY embedding <=> $1::vector
LIMIT 10;
```

## Chunking for Second Brain .md Files

Recommended strategy for markdown knowledge files:
```python
def chunk_markdown(text: str, max_tokens: int = 400, overlap: int = 60):
    """
    Split at H2/H3 boundaries first, then by paragraph.
    Never split inside a code block.
    """
    # 1. Split at headers (H2/H3 = natural semantic breaks)
    sections = re.split(r'\n(?=## |### )', text)
    
    chunks = []
    for section in sections:
        if count_tokens(section) <= max_tokens:
            chunks.append(section)
        else:
            # Further split by paragraph within long sections
            paragraphs = section.split('\n\n')
            current = []
            current_tokens = 0
            for para in paragraphs:
                para_tokens = count_tokens(para)
                if current_tokens + para_tokens > max_tokens and current:
                    chunks.append('\n\n'.join(current))
                    # Overlap: keep last paragraph for context
                    current = current[-1:] if overlap > 0 else []
                    current_tokens = count_tokens(current[0]) if current else 0
                current.append(para)
                current_tokens += para_tokens
            if current:
                chunks.append('\n\n'.join(current))
    return chunks
```

## Hybrid Retrieval (dense + sparse)

```python
# Reciprocal Rank Fusion — combines semantic and keyword results
def reciprocal_rank_fusion(dense_results, sparse_results, k=60):
    scores = {}
    for rank, doc in enumerate(dense_results):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
    for rank, doc in enumerate(sparse_results):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
    
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

## Query Transformation

```python
# HyDE: generate a hypothetical answer, embed that instead of the query
def hyde_retrieve(query: str, llm, db):
    hypothesis = llm.generate(
        f"Write a document that directly answers: {query}\n"
        f"Be specific and factual:"
    )
    return db.similarity_search(hypothesis, top_k=10)

# Multi-query: generate variations to improve recall
def multi_query_retrieve(query: str, llm, db):
    variations = llm.generate(
        f"Generate 3 different phrasings of: {query}\n"
        f"Return as JSON array:"
    )
    all_results = []
    for variant in variations:
        all_results.extend(db.similarity_search(variant, top_k=5))
    return deduplicate_by_similarity(all_results)
```

## Context Assembly

```python
def assemble_context(chunks, token_budget=3000):
    context = []
    used_tokens = 0
    for chunk in sorted(chunks, key=lambda c: c.score, reverse=True):
        tokens = count_tokens(chunk.text)
        if used_tokens + tokens > token_budget:
            break
        context.append(chunk)
        used_tokens += tokens
    return context
```

## Evaluation Quick Reference

| Metric | Target | Measure With |
|---|---|---|
| Context relevance | > 0.80 | Embedding similarity of chunk vs query |
| Answer faithfulness | > 0.90 | NLI model checking answer vs context |
| Answer relevance | > 0.85 | Embedding similarity of answer vs query |
| Retrieval precision@5 | > 0.70 | Manual annotation on test set |

```python
# RAGAS evaluation
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

results = evaluate(
    dataset,  # {"question": [], "answer": [], "contexts": []}
    metrics=[faithfulness, answer_relevancy, context_precision]
)
print(results)  # {faithfulness: 0.92, answer_relevancy: 0.87, ...}
```
