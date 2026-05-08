# Agent B — RAG Memory Module

## What it does

Agent B gives the Code Reviewer a memory of past pull requests. When a new PR comes in, Agent B:

1. **Stores** the new PR's title, description, and diff into a vector database (ChromaDB locally, Pinecone in production)
2. **Retrieves** the 3 most similar past PRs using semantic search
3. **Detects contradictions** — asks LLaMA if the new code change contradicts any past team decision

## How to run it

```bash
python agents/agent_b.py
```

This will:
- Store 2 sample PRs (one adding async DB calls, one policy PR)
- Run retrieval on a new "sync DB call" PR
- Print whether a contradiction is detected

## How the vectors work

Each PR is embedded as a 1024-dimensional vector using Voyage AI's `voyage-code-2` model. This model is specifically trained on code and understands semantic meaning in diffs and commit messages.

When a new PR arrives, its diff is embedded and compared to all stored PR vectors. The 3 closest PRs (by cosine similarity) are returned as context.

## Storage switch

- If `PINECONE_API_KEY` is set in `.env` → uses Pinecone (production, persistent across restarts)
- If not set → uses ChromaDB in memory (local testing, resets on restart)

## Contradiction detection

The contradiction check sends a prompt to LLaMA3 with:
- The retrieved past decisions
- The new code change

LLaMA responds with YES/NO + reasoning. This gets included in the final review comment.

## Dependencies

- `voyageai` — embeddings
- `chromadb` — local vector store
- `pinecone-client` — production vector store
