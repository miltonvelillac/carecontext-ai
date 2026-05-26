FROM python:3.12-slim

WORKDIR /app

COPY packages/carecontext-contracts ./packages/carecontext-contracts
COPY services/document-mcp-server/pyproject.toml ./services/document-mcp-server/
RUN pip install --no-cache-dir ./packages/carecontext-contracts ./services/document-mcp-server

COPY services/document-mcp-server/server.py ./server.py

CMD ["python", "server.py"]
