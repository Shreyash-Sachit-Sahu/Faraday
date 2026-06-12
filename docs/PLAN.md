# Faraday build plan

- [x] **Phase 0 — Scaffold**: repo tree, docker compose (Postgres/Qdrant/Neo4j),
      env templates, CLAUDE.md, health-check FastAPI service
- [x] **Phase 1 — Data pipeline**: HuggingFace datasets → clean → chunk →
      embed → Qdrant, plus BM25 index
      — Phase 1 results: 4,266 articles accepted, 39,281 total chunks
      (wikipedia 20,777 / mmlu 619 / codealpaca 17,885), Qdrant count 39,281
- [x] **Phase 2 — Hybrid retrieval**: dense + BM25 → RRF fusion →
      cross-encoder rerank, with eval harness (precision@5, recall@10, MRR@10)
      — Phase 2 results: MRR@10 bm25 0.970 / dense 0.987 / rrf 0.987 /
      rrf_rerank 0.994
- [x] **Phase 2.5 — Async retrieval service**: warm-start FastAPI /retrieve,
      parallel BM25+dense legs, TTL cache, semaphore backpressure (503 +
      Retry-After), /metrics, Locust load baseline
      — Phase 2.5 results: cache-hot 102.7 RPS at u=16 (p95 99 ms) ≈ 5.3M
      req/day per replica at 60% util, 1M/day ≈ 1 replica; cache-cold
      2.5 RPS (p95 470 ms) ≈ 130k req/day, 1M/day ≈ 8 replicas; zero 500s
      across the ladder, VRAM flat at 1.4 GB
- [ ] **Phase 3 — Graph layer**: NER entity/relation extraction → Neo4j →
      graph-augmented retrieval fused with Phase 2
- [ ] **Phase 4 — QLoRA**: fine-tune Gemma 2 2B, inference endpoint with
      SSE streaming
- [ ] **Phase 5 — Spring Boot**: JWT auth + Google OAuth, Postgres
      persistence, streaming proxy, user document upload with per-user
      scoped retrieval, security hardening
- [ ] **Phase 6 — Frontend**: Next.js hero with scroll animations, auth
      pages, streaming chat UI with user document upload (per-user scoped
      retrieval), end-to-end integration

## Phase 0 tasks
- [x] git init
- [x] directory tree created
- [x] docker-compose.yml, .env.example, .gitignore, CLAUDE.md, README.md
- [x] venv created and requirements installed
- [x] .env filled with generated passwords
- [x] all three containers up
- [x] /health returns ok for qdrant and neo4j
- [x] initial commit
