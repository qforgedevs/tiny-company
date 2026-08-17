# AGENTS.md

## Mission

Tiny Company is a learning laboratory for trustworthy AI-operated businesses. The repository must remain a readable, testable, maintainable monorepo for a simulated recurring-payments academy.

## Non-negotiable invariants

1. The simulator and domain services are authoritative. LLM outputs never directly mutate persistence.
2. Agents use only typed tools. Tools call domain services; tools never mutate tables directly.
3. Every mutating action is authorized, policy-checked, idempotent, and audited.
4. Ground truth is visible only to the evaluator and must never reach normal API responses, agent tools, prompts, or browser state.
5. Model-provider secrets stay server-side and are never committed, logged, returned by APIs, or bundled to the browser.
6. Simulation time and random behavior are deterministic from persisted seed/configuration.
7. Human approval is required for all external-effect equivalents and high-impact state changes in v1.
8. Do not store hidden chain-of-thought. Persist concise decision summaries, tool calls/results after redaction, policy decisions, and traces sufficient for audit/debugging.
9. No default test command may make a paid model-provider call.
10. Prefer a straightforward, well-tested solution over speculative scalability infrastructure.

## Architecture constraints

- Monorepo with `apps/web` and `apps/api`.
- Server-side authoritative logic in FastAPI/Python.
- PostgreSQL via SQLAlchemy + Alembic.
- Next.js + TypeScript web client with OpenAPI-derived client usage.
- Deterministic simulator staying separate from LLM orchestration.
- Model access behind `ModelGateway` abstraction with fake adapter for tests and one real adapter behind server-side environment variables only.
- Server-Sent Events for live updates and audit events.

## Coding conventions

- Keep business logic out of HTTP handlers and React components.
- Prefer small, explicit units with clear service boundaries.
- Use strict TypeScript and explicit Python typing.
- Treat schemas as boundary contracts; validate malformed model/tool output safely.
- Use database transactions around domain mutations.
- Include correlation IDs, run IDs, task IDs, and actor identity in structured logs and audit records.
- Keep comments limited to non-obvious reasoning.
- Prefer iterative clarity over speculative abstraction.

## Testing rules

- Default automated tests must never call a paid provider.
- Domain and policy logic should be unit-tested with deterministic fixtures.
- Persistence tests target disposable PostgreSQL or SQLite-backed transactional test database.
- Simulator determinism tests must assert identical replay results from the same seed/configuration.
- Agent loop tests must cover malformed tool output, tool authorization failures, and idempotency guardrails.
- UI tests must validate loading, empty, error, and critical user flows; no UI dependency on mock-only state once the API exists.
- Build validation must include formatting, linting, typing, unit tests, and relevant integration tests.

## Forbidden shortcuts

- No direct model calls from browser code.
- No direct database mutation from agent tools or route handlers.
- No hidden reasoning logs or chain-of-thought storage.
- No paid-provider calls in default test commands.
- No replacing the approved architecture with a single-language or no-code shortcut.
- No bypassing approval gates for high-impact or external-effect actions.
- No broad speculative infrastructure before the current stage is validated.

## Working protocol

1. Implement stages strictly in blueprint order.
2. Update the implementation-status ledger with tasks, evidence, and next steps for each stage.
3. Validate the relevant commands before claiming completion.
4. Keep docs aligned with code.
5. Commit each completed stage with a clear conventional-commit message.

## Required commands

- `make setup`
- `make test`
- `make lint`
- `make typecheck`
- `make api-health`
- `make web-build`

These commands may evolve as the repo matures, but they must remain simple and reproducible for local developers.
