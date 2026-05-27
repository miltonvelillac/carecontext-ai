# Project Decisions

## Product

- **Audience:** general users.
- **Languages:** bilingual, Spanish and English.
- **Corpus:** curated public seed corpus plus user-uploaded documents.
- **Audio:** speech-to-text input and text-to-speech output.
- **Safety:** educational answers only; no diagnosis or treatment recommendations.

## Safety Behavior

- Normal questions receive grounded answers with citations and a disclaimer.
- Sensitive medical questions receive grounded answers with strong caveats and guidance to seek professional care.
- Crisis, self-harm, or harm-to-others intent bypasses normal RAG and returns immediate help guidance.

## Architecture

- **Frontend:** ReactJS + TypeScript.
- **Backend:** FastAPI + Pydantic.
- **Orchestration:** LangChain baseline; LangGraph only when graph/state or multi-agent flow is useful.
- **LLM workflow standard:** all LLM-mediated workflows in the API Host use LangChain prompt templates and parsers for prompt construction and structured output parsing. Provider adapters only execute model calls behind ports.
- **Provider pattern:** ports/adapters + dependency injection + composition-root factory.
- **Initial real provider:** OpenAI adapters for LLM, embeddings, STT, and TTS.
- **Test providers:** mock/fake providers for deterministic tests.
- **MCP:** included from the start for document and retrieval tooling.
- **MCP transport:** STDIO for local development.
- **Vector DB:** ChromaDB.
- **Deploy:** local Docker first.
- **Evaluation:** lightweight evals initially.

## LangGraph Multi-Agent Strategy

LangGraph will be used where it adds a clear portfolio and engineering benefit,
not as a default replacement for simple service orchestration.

### Query Graph

The query path is the primary LangGraph showcase:

```txt
Safety Agent
  -> Query Router Agent
  -> Retrieval Agent
  -> Synthesis Agent
  -> Citation Critic Agent
```

Expected behavior:

- Crisis or high-risk intent can short-circuit normal RAG.
- Retrieval can be adjusted when context is weak.
- Synthesis must stay grounded in retrieved chunks.
- Citation critique validates whether the answer is sufficiently supported.

### Ingestion Graph

The document ingestion path can also use LangGraph once MCP clients are in place:

```txt
Deterministic Detector
  -> Document Classifier Agent
  -> Router Gate
  -> Document MCP Tool
  -> Metadata Enrichment Agent
  -> Chunking and Indexing
  -> Indexing Verifier Agent
```

The Document Classifier Agent may use an LLM to recommend the document type,
extraction strategy, and MCP server/tool. The recommendation is not executed
directly. A deterministic Router Gate validates it against MIME type, extension,
magic bytes, confidence thresholds, and an allowlist of MCP servers/tools.

This keeps the project agentic while preserving predictable, testable control
over external tool execution.

## Initial Curated Corpus Topics

- Anxiety education.
- Sleep hygiene.
- Stress management.
- General mental wellbeing.
- Educational-use limits and care escalation.
