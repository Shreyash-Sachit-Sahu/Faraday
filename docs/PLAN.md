# Faraday build plan

- [x] **Phase 0 — Scaffold**: repo tree, docker compose (Postgres/Qdrant/Neo4j),
      env templates, CLAUDE.md, health-check FastAPI service
- [x] **Phase 1 — Data pipeline**: HuggingFace datasets → clean → chunk →
      embed → Qdrant, plus BM25 index
      — Phase 1 results: 18,108 Wikipedia articles accepted of 6.4M scanned,
      112,147 total chunks, Qdrant count 112,147
- [x] **Phase 2 — Hybrid retrieval**: dense + BM25 → RRF fusion →
      cross-encoder rerank, with eval harness (precision@5, recall@10, MRR@10)
      — Phase 2 results (re-baselined on 112k-chunk corpus, P@5/R@10/MRR@10):
      bm25 0.598/0.814/0.903 / dense 0.593/0.768/0.960 /
      rrf 0.655/0.854/0.965 / rrf_rerank 0.711/0.912/0.992
- [x] **Phase 2.5 — Async retrieval service**: warm-start FastAPI /retrieve,
      parallel BM25+dense legs, TTL cache, semaphore backpressure (503 +
      Retry-After), /metrics, Locust load baseline
      — Phase 2.5 results: cache-hot 102.7 RPS at u=16 (p95 99 ms) ≈ 5.3M
      req/day per replica at 60% util, 1M/day ≈ 1 replica; cache-cold
      2.5 RPS (p95 470 ms) ≈ 130k req/day, 1M/day ≈ 8 replicas; zero 500s
      across the ladder, VRAM flat at 1.4 GB
- [x] **Phase 3 — Graph layer**: GLiNER entity extraction → Neo4j co-occurrence
      graph → graph-hop retrieval fused as a third RRF leg, fifth eval column
      — Phase 3 results: graph 109,815 chunks / 231,753 entities / 662,289
      MENTIONS / 51,879 CO_OCCURS, coverage 0.979; MRR@10 bm25 0.903 /
      dense 0.960 / rrf 0.965 / rrf_rerank 0.992 / rrf_rerank_graph 0.992
      (graph delta P@5 +0.000 / R@10 +0.002 / MRR@10 +0.000 — HEALTHY: graph
      metric-neutral on factoid templates, no regression, kept for relational
      queries). Query-time NER on CPU; graph leg ~0.5-1.4s (above 300ms note,
      flagged, not tuned).
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
