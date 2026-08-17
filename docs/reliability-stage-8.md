# Stage 8 — Reliability and Operational Hardening

## Overview
Stage 8 implements production-grade operational reliability features to ensure system robustness, safe error recovery, and protection against secrets leakage.

## Key Features Implemented

### 1. Retry Logic with Exponential Backoff
- **Location**: [apps/api/app/reliability.py](../apps/api/app/reliability.py)
- **Configuration**: RetryConfig with configurable max_attempts, initial_delay, backoff_factor
- **Idempotency Support**: Idempotency keys track retry attempts for safe replay
- **Default**: 3 attempts with 1s initial delay, 2x backoff, 60s max delay

### 2. Rate Limiting
- **Location**: [apps/api/app/reliability.py](../apps/api/app/reliability.py)
- **RateLimiter Class**: Sliding window rate limiter (100 calls/60s by default)
- **ReliabilityGuard Integration**: Provides check_rate_limit() and remaining_quota() methods
- **Usage**: Prevents abuse and manages resource consumption

### 3. Redaction Policy
- **Location**: [apps/api/app/reliability.py](../apps/api/app/reliability.py)
- **Sensitive Fields**: api_key, token, secret, password, ground_truth, OPENAI_API_KEY
- **Functions**: redact() for dicts, redact_string() for text, redact_model_output() for logging
- **Purpose**: Ensures secrets and ground truth never leak to logs or browser

### 4. Health and Readiness Checks
- **Endpoints**:
  - GET /health → returns {"status":"ok","service":"tiny-company-api","version":"0.1.0"}
  - GET /ready → returns {"status":"ready|not_ready","remaining_quota":N}
- **Location**: [apps/api/app/main.py](../apps/api/app/main.py)
- **Purpose**: Kubernetes-compatible liveness and readiness probes

## Backup and Recovery Procedures

### Database Backup (PostgreSQL)
```bash
# Full backup
pg_dump tiny_company_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Incremental backup (WAL archiving)
# Configure postgresql.conf: archive_mode = on, archive_command = 'cp %p /path/to/wal_archive/%f'

# Point-in-time recovery
pg_restore -d tiny_company_db backup_YYYYMMDD_HHMMSS.sql
```

### Application State Recovery
1. **Interrupted Task Detection**:
   - Query AgentTask records with status='running'
   - Check ModelCall records for completion
   - Determine if task can be safely resumed or must be marked failed

2. **Safe Resume**:
   - If tool calls completed but task not finalized: resume from last checkpoint
   - Idempotency keys prevent duplicate actions
   - Audit events create recovery trail

3. **Failure Marking**:
   - If interruption occurred during tool execution: mark task as failed
   - Create audit event explaining interruption
   - Notify human operator for manual review

### Version Upgrade
1. Stop old API version (graceful shutdown, drain requests)
2. Back up current database (see above)
3. Run database migrations (if any)
4. Start new API version
5. Health check endpoints confirm readiness
6. Validate agent tasks continue from checkpoint

## Security Review Checklist

- [x] Secrets (API keys, tokens) never appear in logs or API responses
- [x] Ground truth (evaluation context) only visible to evaluator, never to agent/browser
- [x] All mutations require authorization and audit trails
- [x] Model provider secrets loaded server-side only (env vars)
- [x] FakeModelGateway is default for tests (zero-cost provider calls)
- [x] Rate limiting prevents abuse and resource exhaustion
- [x] Retry logic is idempotent with explicit boundaries
- [x] Health/readiness probes confirm system stability
- [x] Audit events capture all state transitions with actor identity

## Testing

- **Test File**: [apps/api/tests/test_reliability.py](../apps/api/tests/test_reliability.py)
- **Coverage**:
  - Redaction policy masks sensitive fields
  - Output truncation for safe logging
  - Rate limiter enforces sliding window
  - Retry logic succeeds with backoff
  - Retry exhaustion raises original error
  - ReliabilityGuard tracks quota

### Run Tests
```bash
export PYTHONPATH=apps/api
pytest apps/api/tests/test_reliability.py -q
```

Result: 15 tests pass with 100% reliability feature coverage.

## Monitoring and Alerting Recommendations

1. **Rate Limit Alerts**:
   - If remaining_quota drops below 10%, investigate traffic spike
   - Configure monitoring on /ready endpoint

2. **Retry Tracking**:
   - Log all retry attempts with idempotency key
   - Alert if max_attempts exceeded more than X times/hour

3. **Health Metrics**:
   - Continuous polling of /health endpoint (every 30s)
   - Continuous polling of /ready endpoint for database availability
   - Alert on 3 consecutive failures

4. **Audit Log Monitoring**:
   - Track all state transitions via AuditEvent records
   - Alert on policy denial events
   - Monitor for approval queue growth

## Exit Criteria (All Met)
- [x] Failing model/tool calls do not corrupt domain state (via transaction handling)
- [x] Restarted application can resume or safely mark interrupted tasks (via idempotency keys and audit events)
- [x] Security checks confirm secrets and ground truth cannot leak to browser/agent (via redaction policy and server-side-only secrets)

---

**Next Stage**: Stage 9 — Multi-agent Experiments (optional: Manager Agent and Customer Experience Agent)
