# Next Project Proposal: Health & Psychology RAG Assistant

## 1) Vision

Build a portfolio-ready **RAG-first AI assistant** focused on health and psychology educational content. Users can:

- query with text,
- upload their own documents,
- submit audio questions,
- optionally receive spoken answers,
- receive grounded answers with citations from trusted sources.

The primary goal is to demonstrate strong engineering in:

- RAG architecture,
- retrieval quality,
- agent orchestration (single + multi-agent modes),
- evaluation and observability,
- safe handling for sensitive domains.

---

## 2) Problem and Scope

### In scope (MVP)

- Web app (simple dark mode UI).
- Ingestion of curated seed corpus + user-uploaded files (PDF initially).
- Chunking, embeddings, indexing in ChromaDB.
- Text Q&A grounded in retrieved chunks.
- Audio input (speech-to-text) for questions.
- Audio output (text-to-speech) for answers.
- Answer citations with source snippets.
- Basic safety layer and medical disclaimer.

### Out of scope (MVP)

- Clinical diagnosis or treatment recommendations.
- User accounts/roles.
- Multi-tenant enterprise controls.
- Fine-tuned domain models.
- Full EHR integrations.

---

## 3) Product Principles

1. **Grounded by default**: every substantive answer should cite sources.
2. **Safety-first UX**: include disclaimers and escalation guidance for crisis/high-risk queries.
3. **Explainability**: show why chunks were retrieved.
4. **Modularity**: decouple ingestion, retrieval, orchestration, and generation.
5. **Evaluability**: include offline and online quality checks from day one.

---

## 3.1) Locked MVP Decisions

- **Audience:** general users.
- **Languages:** bilingual, Spanish and English.
- **Corpus policy:** combine curated seed corpus and user-uploaded documents.
- **Audio scope:** speech-to-text (STT) and text-to-speech (TTS).
- **Model/provider strategy:** provider-agnostic from day one using ports/adapters, dependency injection, and a composition-root factory.
- **MCP usage:** use MCP from the start for external tool boundaries, beginning with document tools and retrieval tools.
- **Deployment target:** local Docker first.
- **Evaluation depth:** lightweight evals for the MVP.
- **Orchestration:** use LangChain for the baseline RAG workflow; introduce LangGraph when the workflow needs explicit graph/state management or multi-agent coordination.

---

## 4) Suggested Architecture

```txt
ReactJS Frontend (dark mode)
   -> HTTP
FastAPI API Host
   |-- Query Orchestrator
   |     |-- LangChain baseline chain
   |     |-- LangGraph graph when state or multi-agent coordination is needed
   |     |-- Safety step
   |     |-- Retrieval step
   |     |-- Synthesis step
   |     `-- Citation verification step
   |-- Provider ports/adapters
   |     |-- LLM provider
   |     |-- Embeddings provider
   |     |-- STT provider
   |     `-- TTS provider
   |-- DocumentMcpClient -> MCP STDIO -> Document MCP Server
   |-- RetrievalMcpClient -> MCP STDIO -> Retrieval MCP Server
   `-- Local Docker runtime
```

### MCP architecture

To align with the PodCraft pattern, MCP is part of the MVP from the start:

```txt
ReactJS Frontend
   -> HTTP
FastAPI API Host / MCP Host
   |-- Internal Query Orchestrator
   |     |-- LangChain baseline RAG chain
   |     |-- LangGraph graph for multi-agent/stateful workflows when needed
   |     |-- Safety step
   |     |-- Retrieval step
   |     `-- Synthesis/Citation step
   |-- DocumentMcpClient
   |     `-- MCP STDIO -> Document MCP Server
   |           |-- extract_text_from_pdf
   |           |-- clean_extracted_text
   |           `-- get_document_metadata
   |-- RetrievalMcpClient
   |     `-- MCP STDIO -> Retrieval MCP Server
   |           |-- upsert_chunks
   |           |-- hybrid_search
   |           `-- rerank_results
   `-- Audio providers
         |-- speech_to_text
         `-- text_to_speech
```

Rules for MVP:

- Keep **agent reasoning internal** to the API Host (do not make the main orchestrator an MCP server).
- Use MCP servers for **external capabilities/tools** from the start.
- Start with **Document MCP** and **Retrieval MCP** as first-class MVP services.
- Start with **STDIO transport** for local development; evaluate Streamable HTTP after end-to-end stability.
- Keep host-side integration boundaries as dedicated clients (`DocumentMcpClient`, `RetrievalMcpClient`).
- Keep STT/TTS provider-agnostic through ports/adapters. They can become MCP services later only if there is a clear benefit.

### Architecture decision

- Use MCP from the start for document and retrieval tooling.
- Keep orchestration internal to the FastAPI API Host.
- Use LangChain first for the baseline RAG flow.
- Introduce LangGraph only when stateful graph execution or multi-agent coordination becomes useful.

---

## 5) Data & Retrieval Design

### Document types (MVP)

- PDF (required)
- Plain text / markdown (nice to have)

### Metadata schema per chunk

- `doc_id`
- `title`
- `source_type` (uploaded, curated)
- `topic_tags` (anxiety, sleep, stress, cognition, etc.)
- `language`
- `chunk_id`
- `section`
- `created_at`
- `quality_score` (optional)

### Retrieval strategy

1. Query preprocessing (language detect, normalization).
2. Hybrid retrieval:
   - dense vector search (ChromaDB),
   - sparse keyword/BM25 fallback.
3. Reranking (cross-encoder or LLM rerank for top-k).
4. Context packing with token budget and de-duplication.
5. Citation map generated before answer synthesis.

---

## 6) Agent Design (Single vs Multi-Agent)

### Single-agent baseline (must-have first)

- One orchestrator chain:
  - retrieve,
  - synthesize,
  - cite,
  - safety check.

### Multi-agent mode (when needed)

- **Safety Agent:** detects harmful/self-harm/high-risk content and enforces policy response.
- **Retriever Agent:** optimizes search plan (query expansion, top-k, filters).
- **Synthesizer Agent:** composes response grounded in approved chunks.
- **Critic/Citation Agent:** validates claims against citations and flags unsupported statements.

### Ingestion graph mode (portfolio showcase)

- **Deterministic Detector:** inspects MIME type, extension, magic bytes, and basic file signals.
- **Document Classifier Agent:** uses an LLM to recommend document type, extraction strategy, and MCP server/tool.
- **Router Gate:** validates the recommendation against confidence thresholds and an allowlist before any MCP tool runs.
- **Metadata Enrichment Agent:** suggests language, topic tags, sections, and quality signals.
- **Indexing Verifier Agent:** checks that chunks and citations are retrieval-ready.

### Why this split

- Better debuggability.
- Easier evaluation per stage.
- Strong portfolio narrative for agentic decomposition.

---

## 7) Tech Stack Recommendation

- **Frontend:** ReactJS + TypeScript (component-based UI, hooks, dark mode).
- **Backend:** FastAPI + Pydantic.
- **Orchestration:** LangChain for baseline RAG; LangGraph when explicit graph/state or multi-agent coordination is needed.
- **Vector DB:** ChromaDB.
- **Embeddings:** provider-agnostic embeddings interface with configurable adapters.
- **LLM:** provider-agnostic LLM interface with configurable adapters and mock provider for tests.
- **Speech-to-text:** provider-agnostic STT interface.
- **Text-to-speech:** provider-agnostic TTS interface.
- **MCP:** STDIO-based Document MCP Server and Retrieval MCP Server.
- **Observability:** LangSmith + structured logs + trace IDs.
- **Eval:** Ragas or custom retrieval/faithfulness benchmark scripts.

---

## 8) API Proposal (MVP)

- `GET /health`
- `POST /api/ingestion/upload` (multipart file)
- `POST /api/ingestion/curated/sync`
- `POST /api/query/text`
- `POST /api/query/audio`
- `GET /api/documents`
- `GET /api/documents/{doc_id}`

### `POST /api/query/text` response shape

```json
{
  "answer": "...",
  "citations": [
    {
      "doc_id": "doc-123",
      "title": "Sleep Hygiene Basics",
      "chunk_id": "doc-123-chunk-07",
      "snippet": "..."
    }
  ],
  "safety": {
    "risk_level": "low",
    "disclaimer": "Educational information only. Not medical advice."
  }
}
```

---

## 9) Safety & Compliance Baseline

- Always display: "This assistant is educational and not a substitute for professional care."
- Crisis intent detection (self-harm, harm to others) with emergency guidance response template.
- No definitive diagnosis output.
- Prefer uncertainty statements when evidence is weak.
- Keep audit logs of retrieval context and generated answer IDs.

---

## 10) UX (Dark Mode, Minimal)

Single-page app sections:

1. **Upload panel** (PDF + tags).
2. **Corpus panel** (list documents + status indexed).
3. **Ask panel** (text input + audio input).
4. **Audio output controls** (play generated TTS response).
5. **Answer panel** (answer + citations + safety note).

Keep styling intentionally simple (portfolio emphasis on architecture/evaluation).

---

## 11) Evaluation Strategy

### Offline

- Retrieval metrics: Recall@k, MRR.
- Groundedness/faithfulness checks with reference answers.
- Citation precision: percent of claims backed by retrieved chunks.

### Online

- Latency p50/p95.
- Empty retrieval rate.
- Citation click-through/use rate.
- Safety intervention rate.

---

## 12) Repo Strategy (aligned with PodCraft)

Use the same monorepo philosophy:

- `apps/web-react` (or new web app)
- `apps/api-host-rag`
- `services/document-mcp-server` (MVP)
- `services/retrieval-mcp-server` (MVP)
- `docs/` for architecture, evaluation, and safety docs

---

## 13) Delivery Roadmap

1. Project scaffolding and config.
2. Provider-agnostic ports/adapters and dependency injection setup.
3. Document MCP Server and `DocumentMcpClient`.
4. Retrieval MCP Server, chunking, embeddings, and Chroma indexing.
5. Text query endpoint with citations using LangChain baseline RAG.
6. Basic ReactJS UI (dark mode).
7. Audio query endpoint with STT and TTS.
8. Safety layer hardening.
9. Lightweight evaluation harness.
10. LangGraph pass if the orchestration needs graph/state or multi-agent flow.
11. Documentation + demo assets.

---

## 14) Remaining Questions to Finalize Before Build

1. **Safety strictness:** normal questions get grounded answers with citations and a disclaimer; sensitive medical questions get strong caveats; crisis/self-harm/harm-to-others bypass normal RAG and redirect to immediate help guidance.
2. **Initial providers:** OpenAI adapters for LLM, embeddings, STT, and TTS, plus mock providers for tests. The application core remains provider-agnostic.
3. **Curated corpus:** start with 3-5 trusted public documents covering anxiety, sleep, stress, general mental wellbeing, and educational-use limits.
4. **Timeline:** define after the first scaffold and API contracts are in place.

---

## 15) Recommended Next Step

Generate:

- a finalized `README` for the new project,
- detailed folder tree,
- exact API contracts,
- a phased implementation plan with week-by-week milestones.
