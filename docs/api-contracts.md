# API Contracts

Initial MVP endpoints. These contracts are typed by the Pydantic models under
`apps/api-host-rag/app/schemas`.

## Common Enums

```txt
LanguageCode: auto | en | es
SourceType: curated | uploaded
DocumentStatus: uploaded | extracted | indexing | indexed | failed
SafetyRiskLevel: low | medium | high | crisis
SafetyAction: allow | caveat | redirect
```

## `GET /health`

Returns service health.

Response:

```json
{
  "status": "ok"
}
```

## `POST /api/ingestion/upload`

Uploads a user PDF and runs the current ingestion pipeline:

1. Extract text through the Document MCP server.
2. Clean extracted text through the Document MCP server.
3. Infer lightweight metadata through the Document MCP server.
4. Chunk the document through the Retrieval MCP server.
5. Upsert chunks into ChromaDB through the Retrieval MCP server.
6. Store the document read model in the local document repository.

Request:

- `multipart/form-data`
- `file`: PDF file
- `title`: optional string
- `topic_tags`: optional comma-separated string, for example `sleep,stress`
- `language`: optional `auto`, `en`, or `es`

Response model: `IngestionJobResponse`

```json
{
  "doc_id": "upload-sleep.pdf",
  "status": "indexed",
  "source_type": "uploaded",
  "message": "Upload accepted and processed. Inserted chunks: 1.",
  "document": {
    "doc_id": "upload-sleep.pdf",
    "title": "sleep.pdf",
    "source_type": "uploaded",
    "topic_tags": ["sleep", "stress"],
    "language": "auto",
    "status": "indexed",
    "created_at": null,
    "quality_score": null
  }
}
```

## `POST /api/ingestion/curated/sync`

Starts curated corpus synchronization. The current implementation returns a
mock not-implemented response.

Response model: `CuratedSyncResponse`

```json
{
  "status": "not_implemented",
  "indexed_documents": 0,
  "skipped_documents": 0,
  "failed_documents": 0
}
```

## `POST /api/query/text`

Runs a text query through the baseline RAG flow:

1. Classify safety risk.
2. Redirect crisis or high-risk requests before retrieval.
3. Retrieve indexed chunks through the Retrieval MCP server.
4. Synthesize an answer through the configured answer synthesizer.
5. Return citations and retrieved context from the selected chunks.

By default, the app uses mock LLM behavior and deterministic local embeddings.
When configured with OpenAI providers, LLM and embedding calls use the OpenAI
adapters behind the same ports.

Request model: `TextQueryRequest`

```json
{
  "query": "How can sleep routines help with stress?",
  "language": "auto",
  "top_k": 5,
  "filters": {
    "source_types": ["curated"],
    "topic_tags": ["sleep"],
    "language": "auto"
  },
  "include_tts": false
}
```

Response model: `RagAnswerResponse`

```json
{
  "answer": "Consistent sleep routines can support sleep quality and may help with stress management. This assistant is educational and not a substitute for professional care.",
  "citations": [
    {
      "doc_id": "upload-sleep.pdf",
      "title": "Sleep Guide",
      "chunk_id": "upload-sleep.pdf-chunk-001",
      "snippet": "Consistent sleep routines, reduced evening stimulation, and regular wake times can support sleep quality and may help people manage stress.",
      "section": "Sleep routines",
      "score": 0.92,
      "metadata": {
        "filename": "sleep.pdf"
      }
    }
  ],
  "safety": {
    "risk_level": "low",
    "action": "allow",
    "disclaimer": "Educational information only. Not medical advice.",
    "reasons": [],
    "escalation_message": null
  },
  "retrieved_context": [
    {
      "doc_id": "upload-sleep.pdf",
      "title": "Sleep Guide",
      "chunk_id": "upload-sleep.pdf-chunk-001",
      "snippet": "Consistent sleep routines, reduced evening stimulation, and regular wake times can support sleep quality and may help people manage stress.",
      "score": 0.92,
      "section": "Sleep routines",
      "metadata": {
        "filename": "sleep.pdf"
      }
    }
  ],
  "transcription": null,
  "tts": null,
  "trace_id": "mock-trace-text"
}
```

## `POST /api/query/audio`

Accepts audio input as multipart form data, returns mock transcription, then
uses the same mock RAG response contract as text queries.

Request:

- `multipart/form-data`
- `file`: audio file
- `language`: optional `auto`, `en`, or `es`
- `top_k`: optional integer from 1 to 20
- `include_tts`: optional boolean, defaults to `true`

Response model: `RagAnswerResponse`

```json
{
  "answer": "Mock audio answer: the transcribed question was routed through the same placeholder RAG contract used by text queries.",
  "citations": [
    {
      "doc_id": "curated-sleep-basics",
      "title": "Sleep Hygiene Basics",
      "chunk_id": "curated-sleep-basics-chunk-001",
      "snippet": "Consistent sleep routines, reduced evening stimulation, and regular wake times can support sleep quality and may help people manage stress.",
      "section": "Sleep routines",
      "score": 0.92,
      "metadata": {
        "mock": "true"
      }
    }
  ],
  "safety": {
    "risk_level": "low",
    "action": "allow",
    "disclaimer": "Educational information only. Not medical advice.",
    "reasons": [],
    "escalation_message": null
  },
  "retrieved_context": [
    {
      "doc_id": "curated-sleep-basics",
      "title": "Sleep Hygiene Basics",
      "chunk_id": "curated-sleep-basics-chunk-001",
      "snippet": "Consistent sleep routines, reduced evening stimulation, and regular wake times can support sleep quality and may help people manage stress.",
      "score": 0.92,
      "section": "Sleep routines",
      "metadata": {
        "mock": "true"
      }
    }
  ],
  "transcription": {
    "text": "Mock transcription for question.mp3",
    "language": null,
    "provider": "mock",
    "model": "mock-stt",
    "duration_seconds": null
  },
  "tts": {
    "audio_id": "mock-tts",
    "audio_url": null,
    "content_type": "audio/mpeg",
    "provider": "mock",
    "model": "mock-tts",
    "duration_seconds": null
  },
  "trace_id": "mock-trace-audio"
}
```

## `GET /api/documents`

Lists documents stored in the local document repository. Uploaded documents are
saved here after successful indexing.

Response model: `DocumentListResponse`

```json
{
  "documents": [
    {
      "doc_id": "upload-sleep.pdf",
      "title": "Sleep Guide",
      "source_type": "uploaded",
      "language": "en",
      "status": "indexed",
      "topic_tags": ["sleep", "stress"],
      "chunk_count": 1,
      "created_at": null
    }
  ]
}
```

## `GET /api/documents/{doc_id}`

Returns document metadata and indexed chunk summaries from the local document
repository.

Response model: `DocumentDetail`

```json
{
  "doc_id": "upload-sleep.pdf",
  "title": "Sleep Guide",
  "source_type": "uploaded",
  "language": "en",
  "status": "indexed",
  "topic_tags": ["sleep", "stress"],
  "chunk_count": 1,
  "created_at": null,
  "chunks": [
    {
      "doc_id": "upload-sleep.pdf",
      "chunk_id": "upload-sleep.pdf-chunk-001",
      "title": "Sleep Guide",
      "text": "Consistent sleep routines, reduced evening stimulation, and regular wake times can support sleep quality and may help people manage stress.",
      "source_type": "uploaded",
      "topic_tags": ["sleep", "stress"],
      "language": "en",
      "section": "Sleep routines",
      "created_at": null,
      "quality_score": null,
      "metadata": {
        "filename": "sleep.pdf"
      }
    }
  ],
  "metadata": {
    "filename": "sleep.pdf"
  }
}
```
