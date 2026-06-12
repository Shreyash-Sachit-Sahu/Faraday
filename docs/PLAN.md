# Faraday build plan

- [x] **Phase 0 — Scaffold**: repo tree, docker compose (Postgres/Qdrant/Neo4j),
      env templates, CLAUDE.md, health-check FastAPI service
- [ ] **Phase 1 — Data pipeline**: HuggingFace datasets → clean → chunk →
      embed → Qdrant, plus BM25 index
- [ ] **Phase 2 — Hybrid retrieval**: dense + BM25 → RRF fusion →
      cross-encoder rerank, with eval harness
- [ ] **Phase 3 — Graph layer**: NER entity/relation extraction → Neo4j →
      graph-augmented retrieval fused with Phase 2
- [ ] **Phase 4 — QLoRA**: fine-tune Gemma 2 2B, inference endpoint with
      SSE streaming
- [ ] **Phase 5 — Spring Boot**: JWT auth + Google OAuth, Postgres
      persistence, streaming proxy, security hardening
- [ ] **Phase 6 — Frontend**: Next.js hero with scroll animations, auth
      pages, streaming chat UI, end-to-end integration

## Phase 0 tasks
- [x] git init
- [x] directory tree created
- [x] docker-compose.yml, .env.example, .gitignore, CLAUDE.md, README.md
- [x] venv created and requirements installed
- [x] .env filled with generated passwords
- [x] all three containers up
- [x] /health returns ok for qdrant and neo4j
- [x] initial commit
