# Release Checklist (v1.0.0)

## Pre-Release (1 week before)

### Code Freeze
- [ ] Announce code freeze date to team
- [ ] Block direct main branch commits (require PR approval only)
- [ ] Finalize all feature branches to be merged
- [ ] Create release branch: `git checkout -b release/v1.0.0`

### Testing
- [ ] Run full test suite: `make test`
  - Result: ___ tests passed, ___ tests failed
- [ ] Run TypeScript checks: `make typecheck`
  - Result: No errors ✓
- [ ] Run web build: `make web-build`
  - Result: Build succeeded ✓
- [ ] Run linting: `make lint`
  - Result: No warnings ✓
- [ ] Manual smoke testing in staging environment
  - [ ] Create scenario and verify display
  - [ ] Execute agent task and verify completion
  - [ ] Verify approval workflow works end-to-end
  - [ ] Test evaluation harness produces correct scores

### Documentation
- [ ] Update [CHANGELOG.md](../CHANGELOG.md) with release notes
- [ ] Verify [README.md](../README.md) installation steps work
- [ ] Review [AGENTS.md](../AGENTS.md) - no changes needed? ✓
- [ ] Update version in [apps/api/app/main.py](../apps/api/app/main.py)
- [ ] Update version in [apps/web/package.json](../apps/web/package.json)

### Infrastructure
- [ ] Verify staging database has clean data
- [ ] Backup production database
- [ ] Document scaling requirements for production
- [ ] Verify staging environment mirrors production
- [ ] Test health and readiness endpoints on staging
  - [ ] GET /health → {"status":"ok",...}
  - [ ] GET /ready → {"status":"ready",...}

## 48 Hours Before Release

### Security Scan
- [ ] Run dependency vulnerability scan: `make security-scan`
  - Result: ___ vulnerabilities found, ___ fixed
- [ ] Review OPENAI_API_KEY handling
  - [ ] Never committed to repository ✓
  - [ ] Only loaded server-side ✓
  - [ ] Never appears in logs ✓
- [ ] Verify secrets manager access configured
- [ ] Verify encryption for secrets in transit

### Performance Testing
- [ ] Load test API with 100 concurrent users
  - Expected: <500ms 95th percentile response time
  - Actual: ___ ms
- [ ] Monitor database connection pool under load
  - Expected: <80 connections
  - Actual: ___ connections
- [ ] Test rate limiter at 150% normal load
  - Expected: graceful rejection, no crashes
  - Result: ✓

### Database
- [ ] Verify all migrations pass on production schema
  - [ ] Create migration test database
  - [ ] Apply all migrations: `alembic upgrade head`
  - [ ] Verify schema matches code
  - [ ] Test downgrade: `alembic downgrade -1 && alembic upgrade head`
- [ ] Backup current production database
  - File: `backup_pre_release_v1.0.0.dump`
  - Size: ___ GB
  - Verified restored: ✓

### Build and Container Images
- [ ] Build API container: `docker build -t tiny-company-api:v1.0.0 apps/api/`
  - Build time: ___ seconds
  - Image size: ___ MB
  - Scan for vulnerabilities: ___ issues found
- [ ] Build Web container: `docker build -t tiny-company-web:v1.0.0 apps/web/`
  - Build time: ___ seconds
  - Image size: ___ MB
  - Scan for vulnerabilities: ___ issues found
- [ ] Push to registry: `docker push registry.example.com/tiny-company-*:v1.0.0`
- [ ] Verify signatures if using image signing

## 24 Hours Before Release

### Staging Deployment Validation
- [ ] Deploy v1.0.0 to staging from containers
  - [ ] API container started successfully
  - [ ] Web container started successfully
  - [ ] Database migrations applied
- [ ] Run smoke tests on staging
  - [ ] `curl http://staging-api:8000/health` → ok
  - [ ] `curl http://staging-api:8000/ready` → ready
  - [ ] Web application loads
  - [ ] Create scenario: scenario created and displays
  - [ ] Run agent task: task completes successfully
  - [ ] Verify approval workflow: approval request created, approved, executed
- [ ] Load test staging: minimal traffic expected ✓
- [ ] Test rollback from v1.0.0 → v0.9.0
  - [ ] Rollback succeeded
  - [ ] v0.9.0 services operational
  - [ ] Restore v1.0.0 for actual release

### Communication
- [ ] Notify stakeholders of scheduled release time
- [ ] Prepare incident response team assignments
- [ ] Document support escalation procedures
- [ ] Create status page update draft

## Release Day

### Pre-Release (2 hours before)
- [ ] Verify team is assembled and available
- [ ] Conduct final health checks on all systems
  - [ ] Production API responding
  - [ ] Production database connected
  - [ ] Monitoring and alerting operational
  - [ ] Logging aggregation working
- [ ] Take final backup of production database
  - File: `backup_immediate_pre_release.dump`
  - Size: ___ GB
- [ ] Freeze read-only mode on non-critical databases (if applicable)

### Deployment (Production)
- [ ] **START DEPLOYMENT WINDOW**
  - Estimated duration: 30-60 minutes
  - Scope: Full API and Web deployment
  - Rollback plan: Restore to v0.9.0 if needed

- [ ] Deploy API container v1.0.0
  - [ ] Stop old API container
  - [ ] Start new API container: `docker pull && docker run ...`
  - [ ] Wait for health checks to pass (30-60 seconds)
  - [ ] Verify logs: no errors ✓

- [ ] Run database migrations
  - [ ] Apply migrations: `alembic upgrade head`
  - [ ] Verify version: `alembic current`
  - [ ] Verify data integrity: `SELECT COUNT(*) FROM organization;` matches expected

- [ ] Deploy Web container v1.0.0
  - [ ] Stop old Web container
  - [ ] Start new Web container
  - [ ] Wait for startup (10-20 seconds)
  - [ ] Verify: `curl http://localhost:3000/` returns 200

### Immediate Post-Deployment Validation (15 minutes)
- [ ] Verify all endpoints responding
  - [ ] `curl http://api:8000/health` → ok ✓
  - [ ] `curl http://api:8000/ready` → ready ✓
  - [ ] `curl http://web:3000/` → 200 ✓
- [ ] Check application logs for errors
  - [ ] No ERROR level logs ✓
  - [ ] No CRITICAL level logs ✓
- [ ] Verify database connectivity
  - [ ] API can read from database ✓
  - [ ] API can write to database ✓
- [ ] Smoke test: Create and execute basic scenario
  - [ ] Scenario created successfully
  - [ ] Displays in dashboard
  - [ ] Agent task runs and completes
- [ ] Error rate monitoring
  - [ ] Error rate <0.5% ✓
  - [ ] Response times normal ✓

### Gradual Traffic Ramp (if using load balancer)
- [ ] Route 10% traffic to v1.0.0
- [ ] Monitor for 5 minutes
  - [ ] Error rate acceptable ✓
  - [ ] Response times acceptable ✓
- [ ] Route 50% traffic to v1.0.0
- [ ] Monitor for 10 minutes
  - [ ] Error rate acceptable ✓
  - [ ] Response times acceptable ✓
- [ ] Route 100% traffic to v1.0.0
- [ ] Continue monitoring for 30 minutes

### Announce Release
- [ ] Update status page: "v1.0.0 deployed successfully"
- [ ] Send notification to stakeholders
- [ ] Close deployment window

## Post-Release (next 24 hours)

### Continuous Monitoring
- [ ] Monitor error rates
  - Expected: <0.5%
  - Actual: __%
- [ ] Monitor response times
  - Expected: <500ms 95th percentile
  - Actual: ___ ms
- [ ] Monitor database performance
  - Active connections: ___ / 100
  - Slow query log: ___ queries over 1s
- [ ] Monitor rate limiter
  - Expected: 0 rejections
  - Actual: ___ rejections
- [ ] Review application logs daily
  - [ ] No unexpected ERROR logs
  - [ ] No repeated patterns

### User Reports
- [ ] Monitor support channels for issues
  - [ ] Slack #support channel
  - [ ] Email support inbox
  - [ ] Status page comments
- [ ] Investigate and resolve any bugs immediately

### Rollback Contingency
- [ ] If critical issue found:
  - [ ] Notify team immediately
  - [ ] Execute rollback: `docker stop api web && docker run ... v0.9.0`
  - [ ] Run rollback validation
  - [ ] Notify stakeholders of rollback
  - [ ] Post-mortem scheduled

## Post-Release (1 week)

### Retrospective
- [ ] Schedule retrospective meeting
- [ ] Document what went well
- [ ] Document what could be improved
- [ ] Assign action items
- [ ] Create GitHub issues for improvements

### Documentation
- [ ] Update [docs/runbooks/deployment.md](runbooks/deployment.md) with lessons learned
- [ ] Document any manual steps or workarounds
- [ ] Update troubleshooting guide

### Release Branch Cleanup
- [ ] Merge release branch back to main: `git checkout main && git merge release/v1.0.0`
- [ ] Create release tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
- [ ] Push to repository: `git push origin main && git push origin v1.0.0`
- [ ] Delete release branch: `git branch -d release/v1.0.0`

## Sign-Off

- **Release Manager**: __________________ Date: __________
- **Engineering Lead**: __________________ Date: __________
- **Operations**: __________________ Date: __________
- **Product Owner**: __________________ Date: __________

---

## Appendices

### Rollback Decision Tree

```
Is v1.0.0 stable?
├─ Yes: Continue monitoring
└─ No:
   ├─ Error rate > 1%?
   │  └─ Yes: Rollback to v0.9.0
   ├─ Response time > 1000ms?
   │  └─ Yes: Investigate, consider rollback
   ├─ Database connection errors?
   │  └─ Yes: Check database, consider rollback
   └─ User-facing feature broken?
      └─ Yes: Rollback to v0.9.0
```

### Key Contacts

- **On-Call Engineer**: _______________________
- **Engineering Lead**: _______________________
- **Product Manager**: _______________________
- **DevOps Lead**: _______________________
- **CEO/Founder**: _______________________

### Communication Templates

**Status Update (Good)**
> v1.0.0 release complete. All systems operational. No issues detected.

**Status Update (Issue)**
> v1.0.0 deployment in progress. Investigating [issue]. ETA to resolution: [time].

**Rollback Announcement**
> v1.0.0 rollback executed due to [reason]. v0.9.0 is now active. We will provide a post-mortem within 24 hours.

