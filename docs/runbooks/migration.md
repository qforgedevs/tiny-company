# Migration and Rollback Runbook

## Database Migrations

### Pre-Migration Planning

**1. Review Changes**
```bash
# Check what migrations will be applied
cd apps/api
alembic heads
alembic current

# Generate migration script
alembic revision --autogenerate -m "describe_changes_here"

# Review generated migration
cat alembic/versions/xxxx_describe_changes.py
```

**2. Backup Production Database**
```bash
# Full backup before any changes
pg_dump -h $DB_HOST -U $DB_USER -Fc $DB_NAME > backup_before_migration_$(date +%Y%m%d_%H%M%S).dump

# Verify backup
pg_restore -d test_db_tmp -l backup_before_migration_*.dump | head
```

**3. Test on Staging**
```bash
# Restore backup to staging database
pg_restore -d staging_db backup_before_migration_*.dump

# Test migration on staging
cd apps/api
export DATABASE_URL=postgresql://user:pass@staging:5432/staging_db
alembic upgrade head

# Run test suite
export PYTHONPATH=apps/api
pytest apps/api/tests/ -q
```

### Executing Migration

**1. Zero-Downtime Migration (if possible)**
```bash
# For simple schema changes (add column, add index)
cd apps/api
export DATABASE_URL=$PRODUCTION_DB_URL
alembic upgrade head

# Verify migration
alembic current
```

**2. With Maintenance Window (for complex changes)**
```bash
# 1. Notify users of maintenance window
# 2. Drain connections
docker-compose pause api

# 3. Backup production database
pg_dump -h $DB_HOST -U $DB_USER -Fc $DB_NAME > backup_maintenance_$(date +%Y%m%d_%H%M%S).dump

# 4. Apply migration
cd apps/api
export DATABASE_URL=$PRODUCTION_DB_URL
alembic upgrade head

# 5. Verify migration
alembic current
SELECT COUNT(*) FROM organization;

# 6. Restart services
docker-compose unpause api

# 7. Run smoke tests
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

### Post-Migration Verification

```bash
# Check alembic version
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"

# Verify schema
psql $DATABASE_URL -c "\dt"

# Check data integrity
psql $DATABASE_URL -c "SELECT COUNT(*) FROM organization;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM customer;"

# Monitor application logs for errors
docker-compose logs -f api | grep -i error
```

## Rollback Procedures

### Automated Rollback (via Alembic)

**For simple migrations (1-2 revisions back):**

```bash
# 1. Stop application
docker-compose stop api

# 2. Identify current version
cd apps/api
alembic current

# 3. Downgrade one revision
alembic downgrade -1

# 4. Verify downgrade
alembic current

# 5. Restart application
docker-compose start api

# 6. Verify service health
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

### Manual Rollback (from backup)

**If automated downgrade fails or data is corrupted:**

```bash
# 1. Stop all services
docker-compose down

# 2. Identify correct backup
ls -lh backup_before_migration_*.dump

# 3. Restore from backup
# DANGER: This will overwrite all data since backup
pg_restore --clean --if-exists -d tiny_company_db backup_before_migration_YYYYMMDD_HHMMSS.dump

# 4. Verify restoration
psql $DATABASE_URL -c "SELECT COUNT(*) FROM organization;"
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"

# 5. Restart services
docker-compose up -d

# 6. Verify health
curl http://localhost:8000/health
```

### Partial Rollback (if specific tables affected)

```bash
# 1. Identify which table has issues
# Example: if new_column has bad data

# 2. Backup current state
pg_dump -h $DB_HOST -U $DB_USER -t table_name $DB_NAME > table_backup.sql

# 3. Fix data
# Option A: Restore from backup version
pg_restore -d tiny_company_db -t table_name backup_before_migration_*.dump

# Option B: Manual SQL cleanup
psql $DATABASE_URL -c "DELETE FROM table_name WHERE new_column IS NULL;"

# 4. Restart application
docker-compose restart api

# 5. Verify
curl http://localhost:8000/health
```

## Testing Rollback Procedure

**Before production deployment, always test rollback:**

```bash
# 1. Restore backup to test database
pg_restore -d test_rollback_db backup_before_migration_*.dump

# 2. Apply migration
cd apps/api
export DATABASE_URL=postgresql://user:pass@localhost:5432/test_rollback_db
alembic upgrade head

# 3. Verify migration worked
alembic current
psql postgresql://user:pass@localhost:5432/test_rollback_db -c "SELECT COUNT(*) FROM organization;"

# 4. Downgrade migration
alembic downgrade -1

# 5. Verify downgrade worked
alembic current
psql postgresql://user:pass@localhost:5432/test_rollback_db -c "SELECT COUNT(*) FROM organization;"

# 6. Upgrade again to confirm idempotency
alembic upgrade head
alembic current
```

## Monitoring After Migration

### Key Metrics

```bash
# Query latency (should not increase significantly)
docker-compose logs api | grep response_time

# Error rate (should be zero)
docker-compose logs api | grep ERROR | wc -l

# Database connection pool usage
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Task completion time (should not degrade)
curl http://localhost:8000/organizations/1/agent-tasks?limit=10
```

### Common Issues

| Issue | Cause | Resolution |
|-------|-------|-----------|
| Connection pool exhausted | Migration didn't complete | Rollback and investigate migration |
| Query timeout errors | New index needs building | Run manual index build in maintenance window |
| Data inconsistency | Partial migration failure | Restore from backup, retry migration |
| Application won't start | Schema mismatch | Verify alembic version matches code version |

## Emergency Rollback

**If production is down and needs immediate recovery:**

```bash
# 1. Identify last known-good backup
ls -lht backup_*.dump | head -5

# 2. Restore immediately (may lose recent data)
pg_restore --clean --if-exists -d tiny_company_db backup_before_migration_*.dump 2>&1 | head -20

# 3. Check if databases came back up
psql $DATABASE_URL -c "SELECT 1"

# 4. Restart all services
docker-compose up -d

# 5. Verify health
sleep 5
curl http://localhost:8000/health

# 6. Post incident review
# Document what failed and why
# Schedule detailed analysis
```

## Preventing Migration Failures

1. **Test migrations on CI/CD pipeline**
   - Run against PostgreSQL 15 on every pull request
   - Verify forward and backward compatibility

2. **Require code review for migrations**
   - At least 2 approvers for any schema changes
   - Document why each change is necessary

3. **Keep migrations small and focused**
   - One schema change per migration
   - Easier to test, debug, and rollback

4. **Use deployment windows for risky changes**
   - Complex data transformations
   - Large table modifications
   - Changes affecting high-volume operations

5. **Maintain comprehensive backups**
   - Daily full backups
   - Test restore procedure monthly
   - Keep at least 30 days of backups

---

**Reference**: See [deployment.md](deployment.md) for general deployment procedures.
