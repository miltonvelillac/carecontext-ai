# API Contracts

Initial MVP endpoints.

## `GET /health`

Returns service health.

```json
{
  "status": "ok"
}
```

## `POST /api/ingestion/upload`

Uploads a user document for extraction, chunking, and indexing.

Request:

- `multipart/form-data`
- `file`: PDF file
- `topic_tags`: optional comma-separated tags
- `language`: optional `en`, `es`, or `auto`

## `POST /api/ingestion/curated/sync`

Indexes the curated seed corpus.

## `POST /api/query/text`

Request:

```json
{
  "query": "How can sleep routines help with stress?",
  "language": "auto",
  "top_k": 5
}
```

Response:

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

## `POST /api/query/audio`

Accepts audio input, transcribes it, runs the text query flow, and optionally returns TTS output metadata.

## `GET /api/documents`

Lists documents and indexing status.

## `GET /api/documents/{doc_id}`

Returns document metadata and indexed chunk summary.

