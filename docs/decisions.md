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
- **Provider pattern:** ports/adapters + dependency injection + composition-root factory.
- **Initial real provider:** OpenAI adapters for LLM, embeddings, STT, and TTS.
- **Test providers:** mock/fake providers for deterministic tests.
- **MCP:** included from the start for document and retrieval tooling.
- **MCP transport:** STDIO for local development.
- **Vector DB:** ChromaDB.
- **Deploy:** local Docker first.
- **Evaluation:** lightweight evals initially.

## Initial Curated Corpus Topics

- Anxiety education.
- Sleep hygiene.
- Stress management.
- General mental wellbeing.
- Educational-use limits and care escalation.

