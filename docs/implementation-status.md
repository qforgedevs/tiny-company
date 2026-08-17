# Tiny Company Implementation Status

This document tracks work against the approved blueprint in [docs/implementation-blueprint.md](docs/implementation-blueprint.md). Each stage below records the scope, concrete evidence, and current status.

## Stage 0 — Repository foundation
- Status: completed
- Scope:
  - monorepo bootstrap
  - root AGENTS.md with invariants and coding rules
  - Docker Compose/PostgreSQL
  - environment templates
  - linting, formatting, typecheck, tests, and CI skeleton
  - README and clean local install documentation
- Acceptance criteria:
  - clean install works from documented commands
  - web and API health endpoints run locally
  - quality commands succeed in a functional baseline
- Relevant files:
  - [AGENTS.md](../AGENTS.md)
  - [README.md](../README.md)
  - [compose.yaml](../compose.yaml)
  - [Makefile](../Makefile)
  - [apps/api/app/main.py](../apps/api/app/main.py)
  - [apps/web/package.json](../apps/web/package.json)
- Evidence:
  - `make test && make typecheck && make web-build && make api-health`
  - Result: 4 API/web tests passed; Next.js production build succeeded; API health endpoint returned `{"status":"ok","service":"tiny-company-api","version":"0.1.0"}`
- Next stage: Stage 1

## Stage 1 — Domain kernel and persistence
- Status: completed
- Scope:
  - database schema and migrations
  - domain glossary and invariants
  - service layer for customers, charges, transactions, messages, cases, approvals, and audit events
  - seeded academy fixture
  - API endpoints for read-only domain exploration
- Acceptance criteria:
  - migrations apply to an empty database
  - database constraints reject invalid relationships
  - domain-service tests cover core invariants
  - API client is generated and used by the web app
- Relevant files:
  - [apps/api/app/models.py](../apps/api/app/models.py)
  - [apps/api/app/services.py](../apps/api/app/services.py)
  - [apps/api/app/main.py](../apps/api/app/main.py)
  - [apps/api/app/schemas.py](../apps/api/app/schemas.py)
  - [apps/api/alembic/env.py](../apps/api/alembic/env.py)
  - [docs/domain-glossary.md](domain-glossary.md)
- Evidence:
  - `export PYTHONPATH=apps/api && pytest apps/api/tests/test_health.py apps/api/tests/test_domain_kernel.py -q`
  - Result: 4 passed in 2.19s
  - `cd apps/web && npm run typecheck && npm run build`
  - Result: Next.js build passed
- Next stage: Stage 2

## Stage 2 — Deterministic simulator
- Status: completed
- Scope:
  - `ScenarioConfig`, `SimulationRun`, event schedule, seed handling, and simulated clock
  - initial payment/message event generators
  - start, pause, advance, reset, and replay API operations
  - persisted simulation and audit events
- Acceptance criteria:
  - identical seed/config produces identical events and state
  - reset/replay reproduces state
  - ground truth remains inaccessible through normal API and agent context
  - tests prove determinism and event ordering
- Relevant files:
  - [apps/api/app/simulator.py](../apps/api/app/simulator.py)
  - [apps/api/app/main.py](../apps/api/app/main.py)
  - [apps/api/tests/test_simulator.py](../apps/api/tests/test_simulator.py)
- Evidence:
  - `pytest apps/api/tests/test_simulator.py -q`
  - Result: 3 passed in 0.03s
  - API contract validation via `TestClient` confirmed `/simulator/run`, `/simulator/run/{run_id}/advance`, `/simulator/run/{run_id}/reset`, and `/simulator/run/{run_id}/replay` all respond deterministically
- Next stage: Stage 3

## Stage 3 — Operations UI
- Status: not_started
- Scope:
  - scenario/run dashboard
  - simulation clock and controls
  - inbox, customer account, transaction, charge, case, and audit views
  - SSE live update stream
  - accessible loading, empty, and error states
- Acceptance criteria:
  - create scenario, advance time, inspect generated records
  - critical flow passes Playwright tests
  - no UI depends on mock data once the API exists
- Relevant files:
  - [apps/web](../apps/web)
- Evidence: pending
- Next stage: Stage 4

## Stage 4 — Policy and approval engine
- Status: not_started
- Scope:
  - declarative policy definitions
  - policy decision service
  - approval-request lifecycle
  - UI for approve/reject/amend with immutable audit events
  - idempotent mutation boundary
- Acceptance criteria:
  - actions requiring approval cannot mutate state before approval
  - duplicate submissions do not produce duplicate state changes
  - approved/rejected actions are traceable
- Relevant files:
  - [apps/api/app](../apps/api/app)
  - [apps/web](../apps/web)
- Evidence: pending
- Next stage: Stage 5

## Stage 5 — Model gateway and single-agent vertical slice
- Status: not_started
- Scope:
  - provider-neutral model interface
  - fake deterministic adapter for tests
  - one real provider adapter behind server-side environment variables
  - Collections Agent orchestration
  - typed tool registry and execution loop
  - persisted task/tool/model records
  - live activity view
- Acceptance criteria:
  - agent handles a single unmatched-payment event by proposing a match or escalating it
  - prompt/provider failures are visible and recoverable
  - no production key appears in browser bundles, logs, or repository
  - tests run against the fake adapter without paid model calls
- Relevant files:
  - [apps/api/app](../apps/api/app)
- Evidence: pending
- Next stage: Stage 6

## Stage 6 — Supervised collections workflow
- Status: not_started
- Scope:
  - payment-match review workflow
  - reminder drafting workflow
  - approval execution tools
  - explicit no-action/escalation outcomes
  - configurable autonomy policy
- Acceptance criteria:
  - accepted match updates the correct charge exactly once
  - ambiguous matches remain unexecuted and are escalated
  - a reminder cannot be sent without approval
  - audit timeline explains outcome without hidden reasoning
- Relevant files:
  - [apps/api/app](../apps/api/app)
- Evidence: pending
- Next stage: Stage 7

## Stage 7 — Evaluation suite
- Status: not_started
- Scope:
  - scenario catalog and evaluation fixtures
  - evaluator that compares outcomes with hidden ground truth
  - CLI/API evaluation runner
  - evaluation persistence and comparison UI
  - regression thresholds in CI
- Acceptance criteria:
  - at least ten representative cases
  - evaluation score is reproducible using the fake model
  - failures produce actionable reports
- Relevant files:
  - [docs/evaluation-spec.md](evaluation-spec.md)
  - [apps/api/app](../apps/api/app)
- Evidence: pending
- Next stage: Stage 8

## Stage 8 — Reliability and operational hardening
- Status: not_started
- Scope:
  - retries with explicit boundaries and idempotency
  - rate limiting and per-run concurrency limits
  - redaction policy for logs and model payloads
  - health/readiness checks
  - error monitoring integration abstraction
  - backup/restore documentation
  - security review checklist
- Acceptance criteria:
  - failing model/tool calls do not corrupt domain state
  - restarted application resumes safely
  - security checks confirm secrets and ground truth cannot leak to browser/agent
- Relevant files:
  - [docs/runbooks](runbooks)
  - [apps/api/app](../apps/api/app)
- Evidence: pending
- Next stage: Stage 9

## Stage 9 — Multi-agent experiments
- Status: not_started
- Scope:
  - optional Manager Agent and Customer Experience Agent
  - agent handoff protocol based on structured tasks
  - role/tool/policy isolation
  - comparative evaluations
- Acceptance criteria:
  - every handoff is visible and auditable
  - specialized-agent configuration produces documented results
  - complexity remains only with evaluation evidence
- Relevant files:
  - [apps/api/app](../apps/api/app)
- Evidence: pending
- Next stage: Stage 10

## Stage 10 — Deployment and release
- Status: not_started
- Scope:
  - production container builds
  - staging environment configuration
  - migration and rollback runbooks
  - CI gates, dependency/security scans
  - deployment and smoke-test workflow
  - release checklist and demo scenario
- Acceptance criteria:
  - clean deploy from documented process
  - migrations and rollback tested in staging
  - demo scenario completes reliably
  - documentation is accurate
- Relevant files:
  - [Makefile](../Makefile)
  - [compose.yaml](../compose.yaml)
  - [docs/runbooks](runbooks)
- Evidence: pending
- Next stage: none
