# CareContext AI

Portfolio-ready RAG-first assistant for educational health and psychology content.

CareContext AI is intentionally educational. It is not a diagnostic or treatment
system and should not be used as a substitute for professional care.

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

## Current Implementation Status

Implemented:

- FastAPI API host with health, ingestion, query, and document routes.
- Provider-agnostic LLM, retrieval, document, STT, and TTS ports.
- LangChain-backed answer synthesis and safety classification.
- STDIO Document MCP server with PDF extraction, text cleaning, and lightweight metadata.
- STDIO Retrieval MCP server with chunking, ChromaDB indexing, hybrid search, and reranking.
- Upload pipeline that extracts PDF text, chunks it, indexes it in ChromaDB, and stores document read models locally.
- Text query path that applies safety classification, retrieves indexed chunks, synthesizes an answer, and returns citations.
- Mock and OpenAI LLM adapters, plus deterministic retrieval embeddings for local tests.
- Backend test coverage for safety, synthesis, DI, MCP clients, retrieval flow, and retrieval scoring.

Partially implemented:

- React app shell exists, but the UI is still static and not connected to API endpoints.
- Audio contracts exist, but STT/TTS behavior still uses mock transcription and mock TTS metadata.
- Curated corpus sync endpoint exists, but the sync pipeline is not implemented yet.
- Evaluation folder exists, but retrieval/faithfulness eval scripts still need to be added.

## Next Implementation Milestones

1. Implement curated corpus sync with 3-5 trusted seed documents.
2. Connect the React UI to upload, corpus, text query, citations, and safety output.
3. Add real STT and TTS provider adapters behind the existing speech ports.
4. Add lightweight retrieval and citation evaluation scripts.
5. Add observability fields such as request trace IDs, retrieval logs, and latency metrics.

## Local Development

Backend tests:

```bash
cd apps/api-host-rag
uv run pytest
```

Frontend build:

```bash
cd apps/web-react
npm install
npm run build
```

Docker runtime:

```bash
docker compose up --build
```

The API is exposed on `http://localhost:8000`, the web app on
`http://localhost:5173`, and ChromaDB on host port `8001`.
