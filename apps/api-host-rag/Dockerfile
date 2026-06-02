FROM python:3.12-slim

WORKDIR /app

COPY packages/carecontext-contracts ./packages/carecontext-contracts
COPY apps/api-host-rag/pyproject.toml ./apps/api-host-rag/
RUN pip install --no-cache-dir ./packages/carecontext-contracts ./apps/api-host-rag

COPY apps/api-host-rag/app ./app
COPY services/document-mcp-server/document_processing.py ./services/document-mcp-server/document_processing.py
COPY services/document-mcp-server/server.py ./services/document-mcp-server/server.py
COPY services/retrieval-mcp-server/adapters ./services/retrieval-mcp-server/adapters
COPY services/retrieval-mcp-server/composition ./services/retrieval-mcp-server/composition
COPY services/retrieval-mcp-server/core ./services/retrieval-mcp-server/core
COPY services/retrieval-mcp-server/ports ./services/retrieval-mcp-server/ports
COPY services/retrieval-mcp-server/services ./services/retrieval-mcp-server/services
COPY services/retrieval-mcp-server/server.py ./services/retrieval-mcp-server/server.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
