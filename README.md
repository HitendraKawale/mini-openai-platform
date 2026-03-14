# Mini OpenAI Platform

A production-style mini AI platform that exposes OpenAI-like APIs for chat completions, embeddings, and retrieval-augmented generation (RAG).

## Planned Architecture

- API Gateway
- LLM Service
- Embedding Service
- RAG Service
- Qdrant Vector Database
- Prometheus + Grafana
- Docker Compose orchestration
- GitHub Actions CI/CD

## Public Endpoints

- `POST /v1/chat/completions`
- `POST /v1/embeddings`
- `POST /v1/rag/query`
- `POST /v1/documents/upload`

## Goals

- portfolio-quality AI infrastructure project
- microservice architecture
- observability and monitoring
- containerized local development
- production-style engineering practices
