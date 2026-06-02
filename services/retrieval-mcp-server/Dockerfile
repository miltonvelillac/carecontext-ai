FROM python:3.12-slim

WORKDIR /app

COPY packages/carecontext-contracts ./packages/carecontext-contracts
COPY services/retrieval-mcp-server/pyproject.toml ./services/retrieval-mcp-server/
RUN pip install --no-cache-dir ./packages/carecontext-contracts ./services/retrieval-mcp-server

COPY services/retrieval-mcp-server/adapters ./adapters
COPY services/retrieval-mcp-server/composition ./composition
COPY services/retrieval-mcp-server/core ./core
COPY services/retrieval-mcp-server/ports ./ports
COPY services/retrieval-mcp-server/services ./services
COPY services/retrieval-mcp-server/server.py ./server.py

CMD ["python", "server.py"]
