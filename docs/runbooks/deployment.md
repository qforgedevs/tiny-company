# Deployment Runbooks

## Overview
This directory contains runbooks for deploying, monitoring, and maintaining Tiny Company in production.

## Quick Start
1. [Build and Deploy](#build-and-deploy)
2. [Verify Deployment](#verify-deployment)
3. [Rollback Procedure](#rollback-procedure)

## Build and Deploy

### Prerequisites
- Docker and Docker Compose installed
- PostgreSQL 15+ running (or use compose stack)
- OPENAI_API_KEY environment variable set for real model provider
- Git repository with latest code

### Building Images

```bash
# Build API image
cd apps/api
docker build -t tiny-company-api:latest .

# Build Web image  
cd apps/web
docker build -t tiny-company-web:latest .

# Tag for registry (if pushing)
docker tag tiny-company-api:latest registry.example.com/tiny-company-api:v1.0.0
docker tag tiny-company-web:latest registry.example.com/tiny-company-web:v1.0.0

# Push to registry
docker push registry.example.com/tiny-company-api:v1.0.0
docker push registry.example.com/tiny-company-web:v1.0.0
```

### Deploy with Docker Compose

```bash
# Set environment
export OPENAI_API_KEY=sk_live_...
export DATABASE_URL=postgresql://user:password@localhost:5432/tiny_company

# Start stack
docker-compose up -d

# Verify services
docker-compose ps
docker-compose logs -f api web
```

### Deploy to Kubernetes (Example)

```bash
# Build and push images
make docker-build

# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment-api.yaml
kubectl apply -f k8s/deployment-web.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Verify deployment
kubectl get deployments -n tiny-company
kubectl get pods -n tiny-company
kubectl describe pod -n tiny-company <pod-name>
```

## Verify Deployment

### Health Checks

```bash
# API health
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"tiny-company-api","version":"0.1.0"}

# API readiness
curl http://localhost:8000/ready
# Expected: {"status":"ready","service":"tiny-company-api","remaining_quota":...}

# Web health (verify page loads)
curl http://localhost:3000/
```

### Database Verification

```bash
# Connect to database
psql $DATABASE_URL

# Verify tables exist
\dt

# Check migrations applied
SELECT * FROM alembic_version;

# Verify seed data
SELECT COUNT(*) FROM organization;
```

### Smoke Test

```bash
# Create scenario
curl -X POST http://localhost:8000/simulator/run \
  -H "Content-Type: application/json" \
  -d '{
    "seed": 48172,
    "start_time": "2026-01-01T08:00:00Z",
    "scenario_version": "v1",
    "organization_name": "Smoke Test Org"
  }'

# Verify scenario created
curl http://localhost:8000/simulator/run

# List customers
curl http://localhost:8000/organizations/1/customers
```

## Rollback Procedure

### If Deployment Fails

```bash
# Stop current containers
docker-compose stop

# Check last known-good version
docker images | grep tiny-company

# Restart with previous version
export TAG=v0.9.0
docker-compose up -d

# Verify services
docker-compose ps
```

### If Database Migration Fails

```bash
# Connect to database
psql $DATABASE_URL

# Check migration status
SELECT * FROM alembic_version;

# Rollback migration (if supported)
cd apps/api
alembic downgrade -1

# Or restore from backup
pg_restore -d tiny_company_db backup_YYYYMMDD_HHMMSS.sql
```

### If Data Corruption Occurs

```bash
# Step 1: Stop all services
docker-compose down

# Step 2: Restore database from backup
pg_restore -d tiny_company_db backup_YYYYMMDD_HHMMSS.sql

# Step 3: Verify backup integrity
psql $DATABASE_URL -c "SELECT COUNT(*) FROM organization;"

# Step 4: Restart services
docker-compose up -d

# Step 5: Run smoke tests
curl http://localhost:8000/health
```

## Database Backup and Restore

### Backup

```bash
# Full backup
pg_dump -h localhost -U postgres tiny_company_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
pg_dump -h localhost -U postgres tiny_company_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# With custom format for faster restore
pg_dump -h localhost -U postgres -Fc tiny_company_db > backup_$(date +%Y%m%d_%H%M%S).dump
```

### Restore

```bash
# From SQL backup
psql -h localhost -U postgres tiny_company_db < backup_YYYYMMDD_HHMMSS.sql

# From compressed backup
gunzip -c backup_YYYYMMDD_HHMMSS.sql.gz | psql -h localhost -U postgres tiny_company_db

# From custom format (faster)
pg_restore -d tiny_company_db backup_YYYYMMDD_HHMMSS.dump
```

## Monitoring and Alerting

### Container Logs

```bash
# API logs
docker-compose logs -f api

# Web logs
docker-compose logs -f web

# Database logs
docker-compose logs -f db
```

### Key Metrics to Monitor

- **API Response Time**: Should be <500ms for 95th percentile
- **Error Rate**: Should be <0.5% of requests
- **Database Connection Pool**: Monitor active connections (max 100)
- **Rate Limiter**: Track rejections (should be zero under normal load)
- **Agent Task Completion**: Monitor task latency and success rate

### Alerting Rules

```
# Alert if API health check fails
if curl -f http://localhost:8000/health fails for 2 minutes
  then alert "API_HEALTH_CHECK_FAILED"

# Alert if readiness probe fails
if curl -f http://localhost:8000/ready fails for 2 minutes
  then alert "API_NOT_READY"

# Alert if error rate exceeds 1%
if error_rate > 0.01 for 5 minutes
  then alert "API_ERROR_RATE_HIGH"
```

## Production Checklist

- [ ] Database backups configured and tested
- [ ] Logging aggregation set up (ELK/Splunk/etc)
- [ ] APM monitoring active (New Relic/DataDog/etc)
- [ ] Alerting rules configured
- [ ] OPENAI_API_KEY secured in secret management system
- [ ] Database credentials in secure vault
- [ ] Rate limiting thresholds adjusted for production load
- [ ] SSL/TLS certificates configured
- [ ] Load balancer configured and tested
- [ ] CDN configured for static assets
- [ ] Incident response procedures documented
- [ ] On-call rotation established

## Maintenance Windows

### No-Downtime Deployments

```bash
# Scale up to 2 replicas
kubectl scale deployment/api --replicas=2

# Update image on one replica
kubectl set image deployment/api api=registry/tiny-company-api:v1.1.0

# Wait for new replica to be ready
kubectl rollout status deployment/api

# Update second replica
# (K8s will handle this automatically with rolling update strategy)

# Verify both replicas running
kubectl get pods
```

### Database Migrations

```bash
# During maintenance window:
# 1. Stop write operations
# 2. Create backup
pg_dump -h localhost -U postgres tiny_company_db > pre-migration-backup.sql

# 3. Run migration
cd apps/api
alembic upgrade head

# 4. Verify migration
alembic current

# 5. Resume write operations
```

## Security Considerations

- Never commit secrets to repository
- Rotate API keys and database passwords regularly
- Use network policies to restrict traffic between services
- Enable audit logging for all database operations
- Monitor for unusual access patterns
- Keep base images up-to-date (rebuild monthly)
- Scan container images for vulnerabilities before deployment
- Use read-only filesystems where possible
- Run containers as non-root user (already configured in Dockerfile)

---

**Reference**: See [AGENTS.md](../AGENTS.md) for production invariants.
