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
- [x] **Phase 4 — QLoRA**: fine-tune Gemma 2 2B, inference endpoint with
      SSE streaming
      — Phase 4 results: SFT set 3,300 (CodeAlpaca 1,800 + Alpaca 1,500;
      LIMA gated/skipped), 3,135 train / 165 eval. Working rung max_len 256 /
      r16 / attn q,k,v,o / grad_accum 16, 2 epochs / 392 steps / 157 min.
      NO rung fits 4 GB: train peak 5.66 GB (512=6.63 GB) via Windows sysmem
      fallback ~24s/step — fixed ~4.7 GB floor from 4-bit weights + 256k-vocab
      LM-head bf16 dequant + eager attention; ladder levers only touch the
      ~6 MB adapter so can't close the gap (documented, not a failure).
      train_loss 0.8624 / eval_loss 0.8666. Adapter gate PASS: adapter
      completion-loss 0.9211 vs base 1.6712 (delta -0.7500); qualitative shows
      a concise tutor voice vs base's verbose markdown. /chat SSE streams
      sources -> tokens -> done; inference VRAM 3.22 GB (< 4 GB, no spill).
- [x] **Phase 5 — Spring Boot backend**: email/password auth (Argon2id),
      short JWT access + rotating refresh tokens (SHA-256 hashed, server-side
      revocation + reuse detection), Postgres via JPA + Flyway, security
      hardening
      — Phase 5 results: Spring Boot 3.5.15 (pinned to 3.x — start.spring.io
      now defaults to 4.x/Security 7, which would break the Security 6 verbatim
      code), Java 21, jjwt 0.12.6, bouncycastle 1.78.1. Flyway V1 applied +
      Hibernate ddl-auto=validate passed. Hardening verified end to end:
      Argon2id ($argon2id$ hashes), refresh rotation + reuse-detection family
      burn, lockout (423 after 5 fails), fixed-window rate limit (429 +
      Retry-After), Bean Validation (400), generic login errors (no
      enumeration), stateless sessions, CSRF off (bearer-only), locked CORS,
      HSTS/frame-deny/referrer headers, per-user isolation (404, no leak), no
      stacktrace in error bodies. Adaptations: JDBC sslmode=disable (local
      non-TLS Postgres) and @Transactional(noRollbackFor) so the security
      writes that precede the auth-exception throws commit.
- [x] **Phase 5.5 — Spring Boot extras**: Google OAuth sign-in, SSE streaming
      chat proxy (writes messages), user document upload + indexing with
      per-user scoped retrieval
      — Phase 5.5 results: Python /ingest + DELETE /documents (owner-scoped
      Qdrant + graph, embedder regression guard held); google-api-client 2.7.0
      verifies ID tokens, find-or-creates a GOOGLE user, rejects same-email
      LOCAL collision (wired; live token untested — no console Client ID).
      /api/chat relays the Python SSE live (meta→sources→tokens→done; user
      message + conversation persist before streaming, assistant message +
      sources on completion); GET /api/conversations/{id}/messages history.
      Upload: 202 PENDING → @Async indexing → INDEXED w/ chunk_count; delete
      removes file + vectors + graph + row; all doc endpoints owner-scoped.
      Owner-scope proven both directions (user sees own upload as #1 source,
      another user does not). Adaptations: python-multipart added; fixed a
      verbatim KeyError('score') in _add_to_graph dedup; UPLOADS_DIR forward
      slashes (Java .properties \u escape); explicit save() in the @Async
      self-invoked updateStatus so the status transition commits. Deferred:
      multi-turn context (chat is single-turn; history stored, not yet fed
      to the model).
- [x] **Phase 6 — Frontend: animated hero + auth**: Next.js 16 / React 19 /
      Tailwind v4 landing page (field-of-force canvas, Lenis smooth scroll,
      motion scroll-reveals + hero parallax) and email/password + Google auth
      pages
      — Phase 6 results: build clean (Next 16.2.9, Tailwind 4.3, motion 12.40,
      lenis 1.3, geist 1.7). Section 0 design system followed exactly (ink/
      copper/field/volt palette, Fraunces/Geist/Geist Mono roles). Verified:
      cursor-reactive field, scroll reveals, hero parallax; reduced-motion =
      quiet static field + instant reveals; responsive to 375px; visible focus
      rings; zero landing-page console errors. Auth: register→/ with refresh
      stored, session persists across reload (rotate-on-401), lockout message
      surfaces, auth-aware nav. Google button renders but the Client ID's
      Authorized JavaScript origins lack http://localhost:3000 — exact error
      "[GSI_LOGGER]: The given origin is not allowed for the given client ID";
      add that origin in the Google console to complete live sign-in.
      Adaptation: geist package added to A.2 install (B.1 imports it).
- [ ] **Phase 6.5 — Frontend: chat + upload UI**: streaming chat interface,
      document upload UI with per-user scoped retrieval, end-to-end integration

## Phase 0 tasks
- [x] git init
- [x] directory tree created
- [x] docker-compose.yml, .env.example, .gitignore, CLAUDE.md, README.md
- [x] venv created and requirements installed
- [x] .env filled with generated passwords
- [x] all three containers up
- [x] /health returns ok for qdrant and neo4j
- [x] initial commit
