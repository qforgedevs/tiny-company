# Tiny Company

Tiny Company is a deterministic learning laboratory for trustworthy AI-operated businesses. The first vertical is a recurring-payments academy where a simulator creates customers, charges, bank transactions, receipts, and operational events while a supervised Collections Agent reviews and proposes actions under policy and approval controls.

## Repository layout

- `apps/web` — Next.js + TypeScript user interface
- `apps/api` — FastAPI + Python authoritative services, simulator, policy, evaluation, and API
- `packages/api-client` — generated TypeScript client from OpenAPI
- `docs` — architecture, policy, evaluation, ADRs, runbooks, and stage ledger
- `infra` — Docker Compose and environment configuration
- `scripts` — local developer helper scripts

## Local quick start

1. Install dependencies:
   - Python 3.12+
   - Node 20+
   - Docker Desktop or Docker Engine
2. Start PostgreSQL:
   - `docker compose up -d db`
3. Install Python tooling:
   - `cd apps/api && uv venv .venv && . .venv/bin/activate && uv pip install -r requirements.txt`
4. Install web tooling:
   - `cd apps/web && npm install`
5. Run API health check:
   - `cd apps/api && . .venv/bin/activate && uvicorn app.main:app --reload`
6. Run the UI:
   - `cd apps/web && npm run dev`

## Environment templates

- `apps/api/.env.example` for FastAPI settings
- `apps/web/.env.example` for Next.js values
- root `.env.example` for shared compose settings

## Quality gates

- `make lint`
- `make typecheck`
- `make test`
- `make api-health`
- `make web-build`

## Safety model

- The simulator and domain services are authoritative.
- Agent tools never mutate tables directly.
- All mutating actions require policy evaluation and approval in v1.
- Ground truth remains evaluator-only.

## Stage ledger

See [docs/implementation-status.md](docs/implementation-status.md).
