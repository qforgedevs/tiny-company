# ADR 0001: Monorepo server-authoritative architecture

- Status: Accepted
- Date: 2026-08-16

## Context

Tiny Company needs a trustworthy AI business learning lab: deterministic simulator behavior, policy-controlled actions, and observability. The product must remain understandable by developers and safe enough for evaluation, while still supporting a realistic web UI and API surface.

## Decision

We keep a monorepo with `apps/api` as the authoritative domain, policy, simulator, and agent orchestration boundary, and `apps/web` as the presentation layer. The browser never calls model providers directly or handles secrets. Domain services own validation, authorization, idempotency, and audit events.

## Consequences

- Clear boundaries between UI, domain logic, simulator, and automation.
- Easier local development using one repo and shared tooling.
- Need to maintain a generated TypeScript client contract from the API.
- More initial setup overhead than a single app, but better safety and maintainability.
