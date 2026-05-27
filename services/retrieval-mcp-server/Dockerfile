FROM python:3.12-slim

WORKDIR /app

COPY packages/carecontext-contracts ./packages/carecontext-contracts
COPY services/retrieval-mcp-server/pyproject.toml ./services/retrieval-mcp-server/
RUN pip install --no-cache-dir ./packages/carecontext-contracts ./services/retrieval-mcp-server

COPY services/retrieval-mcp-server/document_processing.py ./document_processing.py
COPY services/retrieval-mcp-server/server.py ./server.py

CMD ["python", "server.py"]
