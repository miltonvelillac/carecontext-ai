FROM python:3.12-slim

WORKDIR /app

COPY packages/carecontext-contracts ./packages/carecontext-contracts
COPY apps/api-host-rag/pyproject.toml ./apps/api-host-rag/
RUN pip install --no-cache-dir ./packages/carecontext-contracts ./apps/api-host-rag

COPY apps/api-host-rag/app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
