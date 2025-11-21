# CESAR Ecosystem: Production Deployment Checklist

## 🎯 Pre-Deployment Checklist

### Phase 1: Environment Preparation

- [ ] **CockroachDB Cluster**
  - [ ] Cluster provisioned in target region
  - [ ] Connection string obtained from CockroachDB Console
  - [ ] IP allowlist configured (production IPs added)
  - [ ] SSL certificate downloaded (if using verify-full mode)
  - [ ] Test connection: `python3 test_cockroach_connection.py`

- [ ] **Environment Variables**
  - [ ] `.env.cockroach` file created with production credentials
  - [ ] `ENVIRONMENT=production` set
  - [ ] `COCKROACH_DB_URL` validated
  - [ ] API keys for OpenAI/Anthropic configured
  - [ ] Redis URL configured (for rate limiting)

- [ ] **Dependencies**
  - [ ] Python 3.11+ installed
  - [ ] All packages installed: `pip install -r requirements.txt`
  - [ ] PostgreSQL 14+ running locally (if hybrid mode)
  - [ ] Node.js 18+ installed (for frontend)

---

### Phase 2: Database Setup

- [ ] **Schema Migration**
  - [ ] Run test connection: `python3 test_cockroach_connection.py`
  - [ ] Preview migrations: `./apply_migrations_cockroach.sh --dry-run`
  - [ ] Apply all migrations: `./apply_migrations_cockroach.sh`
  - [ ] Verify schema: `psql $COCKROACH_DB_URL -c '\dt'`
  - [ ] Check migration status: `SELECT * FROM schema_migrations;`

- [ ] **Initial Data Sync**
  - [ ] Run initial sync: `./run_cockroach_sync.sh`
  - [ ] Verify agent count: `SELECT COUNT(*) FROM agents;`
  - [ ] Verify mob aliases: `SELECT metadata->>'mob_alias' FROM agents LIMIT 5;`

- [ ] **Bi-Directional Sync**
  - [ ] Test dry-run: `python3 sync_bidirectional.py --dry-run`
  - [ ] Run first sync: `python3 sync_bidirectional.py`
  - [ ] Setup cron job (see below)

---

### Phase 3: API Deployment

- [ ] **Code Updates**
  - [ ] **CRITICAL**: Update `api/main.py` to import `database_v2` instead of `database`
    ```python
    # OLD: from database import get_db
    # NEW: from api.database_v2 import get_db, init_database
    ```
  - [ ] Add startup initialization:
    ```python
    @app.on_event("startup")
    async def startup():
        init_database()  # Validates CockroachDB connection
    ```

- [ ] **Testing**
  - [ ] Run health check: `curl http://localhost:8000/health`
  - [ ] Check database type: `curl http://localhost:8000/health | jq '.components.database.database'`
  - [ ] Expected: `"cockroachdb"` (not "postgresql")
  - [ ] Test agent endpoint: `curl http://localhost:8000/api/agents`

- [ ] **Production Settings**
  - [ ] Disable debug mode: `DEBUG=False`
  - [ ] Enable HTTPS (reverse proxy)
  - [ ] Configure CORS origins (whitelist frontend domain)
  - [ ] Set rate limiting thresholds
  - [ ] Enable Prometheus metrics

---

### Phase 4: Frontend Deployment

- [ ] **Setup**
  - [ ] Run setup script: `./setup_frontend.sh`
  - [ ] Install dependencies: `cd frontend && npm install`
  - [ ] Configure environment: Edit `frontend/.env.local`
    ```
    NEXT_PUBLIC_API_URL=https://api.cesar.ai
    NEXT_PUBLIC_WS_URL=wss://api.cesar.ai/ws/events
    ```

- [ ] **Build & Deploy**
  - [ ] Build production: `npm run build`
  - [ ] Test locally: `npm run start`
  - [ ] Deploy to Vercel/Netlify/AWS
  - [ ] Verify API connection from production URL

---

### Phase 5: Monitoring & Automation

- [ ] **Cron Jobs**
  - [ ] Add bi-directional sync:
    ```bash
    # Edit crontab: crontab -e
    */5 * * * * cd /path/to/cesar_ecosystem && python3 sync_bidirectional.py >> /var/log/cesar_sync.log 2>&1
    ```
  - [ ] Add health check monitoring:
    ```bash
    */1 * * * * curl -f http://localhost:8000/health || echo "API DOWN" | mail -s "CESAR API Alert" admin@example.com
    ```

- [ ] **Logging**
  - [ ] Create log directory: `sudo mkdir -p /var/log/cesar`
  - [ ] Configure log rotation: `/etc/logrotate.d/cesar`
  - [ ] Test logging: `tail -f /var/log/cesar_sync.log`

- [ ] **Prometheus (if enabled)**
  - [ ] Configure scrape target: `http://localhost:8000/metrics`
  - [ ] Import Grafana dashboards (see `docs/grafana/`)
  - [ ] Set up alerts for:
    - API response time > 500ms
    - Database connection failures
    - Sync lag > 10 minutes

---

### Phase 6: Security Hardening

- [ ] **Database**
  - [ ] Use separate user for API (not root/admin)
  - [ ] Grant minimal permissions: `SELECT, INSERT, UPDATE` only
  - [ ] Enable audit logging in CockroachDB Console
  - [ ] Rotate passwords every 90 days

- [ ] **API**
  - [ ] Enable JWT authentication
  - [ ] Add API key rotation
  - [ ] Configure rate limiting (100 req/min per IP)
  - [ ] Enable HSTS headers
  - [ ] Add CSP headers

- [ ] **Network**
  - [ ] Configure firewall: Only allow necessary ports
  - [ ] Enable DDoS protection (Cloudflare/AWS Shield)
  - [ ] Setup VPN for database access (optional)

---

### Phase 7: Disaster Recovery

- [ ] **Backup Strategy**
  - [ ] Automated CockroachDB backups (daily)
  - [ ] Test restore procedure
  - [ ] Document recovery time objective (RTO): Target = 30 minutes
  - [ ] Document recovery point objective (RPO): Target = 5 minutes

- [ ] **Runbook Creation**
  - [ ] Document: "How to recover from local DB failure"
  - [ ] Document: "How to recover from CockroachDB outage"
  - [ ] Document: "How to roll back a migration"
  - [ ] Document: "How to scale to multi-region"

---

## 🚀 Deployment Day Checklist

### Pre-Deployment (T-1 hour)

- [ ] Announce maintenance window to users
- [ ] Backup current production database
- [ ] Verify rollback plan is ready
- [ ] Ensure team is available for support

### Deployment Steps (T-0)

1. [ ] **Stop current services**
   ```bash
   sudo systemctl stop cesar-api
   sudo systemctl stop cesar-sync
   ```

2. [ ] **Deploy new code**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   ```

3. [ ] **Update database connection**
   ```bash
   # Verify database_v2 is imported in api/main.py
   grep "database_v2" api/main.py
   ```

4. [ ] **Run migrations**
   ```bash
   ./apply_migrations_cockroach.sh
   ```

5. [ ] **Initial sync**
   ```bash
   ./run_cockroach_sync.sh
   ```

6. [ ] **Start services**
   ```bash
   sudo systemctl start cesar-api
   sudo systemctl start cesar-sync
   ```

7. [ ] **Verify health**
   ```bash
   curl http://localhost:8000/health
   # Check database: should be "cockroachdb"
   ```

### Post-Deployment (T+15 minutes)

- [ ] Monitor logs: `tail -f /var/log/cesar_api.log`
- [ ] Check error rates in monitoring dashboard
- [ ] Verify agent count: `SELECT COUNT(*) FROM agents;`
- [ ] Test critical user flows (create agent, run workflow)
- [ ] Monitor sync latency: Check `sync_state` table

### Sign-Off (T+1 hour)

- [ ] All services green in monitoring
- [ ] No error spikes in logs
- [ ] User acceptance testing passed
- [ ] Performance metrics within SLA
- [ ] Announce deployment complete

---

## ⚠️ Rollback Procedure

If deployment fails, execute these steps immediately:

1. **Stop new services**
   ```bash
   sudo systemctl stop cesar-api
   ```

2. **Revert code**
   ```bash
   git reset --hard <previous-commit-hash>
   ```

3. **Restore database** (if migrations failed)
   ```bash
   # Restore from backup
   psql $COCKROACH_DB_URL < backup.sql
   ```

4. **Restart old version**
   ```bash
   sudo systemctl start cesar-api-old
   ```

5. **Notify team & users**

---

## 📊 Post-Deployment Monitoring (7 Days)

### Daily Checks

- [ ] API response time < 200ms (p95)
- [ ] Sync lag < 5 minutes
- [ ] Zero database connection errors
- [ ] Agent task success rate > 95%

### Weekly Review

- [ ] Analyze error logs for patterns
- [ ] Review sync conflict rate (should be < 1%)
- [ ] Check database growth rate
- [ ] Optimize slow queries (if any)
- [ ] Plan capacity scaling (if needed)

---

## 🎉 Success Criteria

Deployment is considered successful when:

✅ All 24 agents synced to CockroachDB
✅ API health check returns "cockroachdb" database type
✅ Frontend dashboard displays live data
✅ Bi-directional sync running every 5 minutes
✅ No critical errors in 24 hours
✅ Response time < 200ms (p95)
✅ Uptime > 99.9%

---

**Date**: __________
**Deployed By**: __________
**Verified By**: __________

---

## 📞 Emergency Contacts

- **CockroachDB Support**: support@cockroachlabs.com
- **Infrastructure On-Call**: [Your PagerDuty]
- **Database Team Lead**: [Contact]
- **API Team Lead**: [Contact]
