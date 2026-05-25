# CareContext AI

Portfolio-ready RAG-first assistant for educational health and psychology content.

## MVP Direction

- ReactJS + TypeScript frontend with a minimal dark mode interface.
- FastAPI backend with provider-agnostic ports/adapters.
- MCP from the start for document and retrieval tooling.
- LangChain for the baseline RAG flow; LangGraph only when explicit state or multi-agent orchestration becomes useful.
- ChromaDB for local vector storage.
- STT and TTS in scope.
- Local Docker deployment first.
- Lightweight evaluation from the beginning.

## Initial Structure

```txt
apps/
  api-host-rag/
  web-react/
services/
  document-mcp-server/
  retrieval-mcp-server/
docs/
evals/
data/
```

## First Implementation Milestones

1. Confirm API contracts and domain models.
2. Implement provider ports and mock providers.
3. Implement Document MCP tools.
4. Implement Retrieval MCP tools with ChromaDB.
5. Add text query endpoint with citations.
6. Add React upload, corpus, ask, answer, and audio controls.
7. Add STT/TTS endpoints.
8. Add lightweight eval scripts.

