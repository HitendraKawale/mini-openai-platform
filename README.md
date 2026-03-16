# Mini OpenAI Platform

This is a production-style AI platform built with FastAPI microservices, Qdrant, Docker Compose, Prometheus and Grafana.

The platform exposes OpenAI-like APIs for:
- chat completions
- embeddings
- document upload
- RAG

---

## Architecture

---

## Services

- **api-gateway** — auth, request IDs, rate limiting, caching, routing
- **llm-service** — text generation using Ollama (`phi3:latest`)
- **embedding-service** — embeddings using `all-MiniLM-L6-v2`
- **rag-service** — ingestion, chunking, retrieval, answer generation
- **qdrant** — vector database
- **prometheus** — metrics
- **grafana** — dashboards

---

## Features
- API gateway routing
- request tracing with X-Request-ID
- API key auth
- rate limiting
- response caching
- persistent Qdrant storage
- Prometheus + Grafana monitoring
- Docker healthchecks
- GitHub Actions CI

## Start the platform
```bash
docker compose -f infrastructure/compose/docker-compose.yml up -d --build
```
## Check Services
```bash
docker compose -f infrastructure/compose/docker-compose.yml ps
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```
## API Examples
### Auth:
```http
Authorization: Bearer dev-secret-key
```
### Chat
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-secret-key" \
  -d '{
    "model": "phi3:latest",
    "messages": [{"role": "user", "content": "Explain what are vector databases briefly."}],
    "temperature": 0.7,
    "max_tokens": 80,
    "stream": false
  }'
```
### Embeddings
```bash
curl -X POST http://localhost:8000/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-secret-key" \
  -d '{
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "input": ["Embeddings help semantic search."]
  }'
```
### Upload document
```bash
curl -X POST http://localhost:8000/v1/documents/upload \
  -H "Authorization: Bearer dev-secret-key" \
  -F "file=@sample_rag.txt"
```
### RAG query
```bash
curl -X POST http://localhost:8000/v1/rag/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-secret-key" \
  -d '{
    "query": "How does retrieval augmented generation work?",
    "top_k": 2
  }'
```
---

## Deployment/infrastructure
```
┌─────────────────────────────────────────────────────┐
│                 Docker Compose Stack                │
│-----------------------------------------------------│
│                                                     │
│  api-gateway        :8000                           │
│  llm-service        :8001                           │
│  embedding-service  :8002                           │
│  rag-service        :8003                           │
│  qdrant             :6333                           │
│  prometheus         :9090                           │
│  grafana            :3000                           │
│                                                     │
└─────────────────────────────────────────────────────┘

Host machine also runs:
┌──────────────────────┐
│        Ollama        │
│       :11434         │
└──────────────────────┘
```
## CI
```bash
pip install -r requirements-dev.txt
pytest tests -q
docker compose -f infrastructure/compose/docker-compose.yml config >/dev/null && echo OK
```
Workflow:
```
.github/workflows/ci.yml
```

