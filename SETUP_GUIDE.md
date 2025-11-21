# 🚀 CESAR Ecosystem CockroachDB Integration - Complete Setup Guide

## 📋 **Complete Step-by-Step Instructions**

Follow these steps in order. Each step includes expected output and troubleshooting.

---

## **STEP 1: Test CockroachDB Connection** ⚡

### Run the test:
```bash
cd "/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem"
python3 test_cockroach_connection.py
```

### Expected Output:
```
================================================================================
🔍 CESAR ECOSYSTEM: COCKROACHDB CONNECTIVITY DIAGNOSTIC
================================================================================

📋 TEST 1: Environment Variable Configuration
✅ COCKROACH_DB_URL found
   Connecting to: ***:***@cesar-ecosystem-10552.jxf.gcp-us-east1.cockroachlabs.cloud:26257/defaultdb

📋 TEST 2: Connection Establishment
   Attempting TCP connection... OK (1500ms)
   ✅ TCP connection established

📋 TEST 3: Cluster Information
   Cluster Version: CockroachDB CCL v25.2.6...
   ✅ Confirmed CockroachDB cluster
   Node count unavailable (not a critical error)

📋 TEST 4: Write Permissions
   Creating test table... OK
   Performing INSERT... OK
   ✅ Write permissions confirmed

📋 TEST 5: Read Performance Benchmark
   Read 1/5: 145.23ms
   Read 2/5: 142.56ms
   ...
   Average Latency: 143.45ms
   ✅ Good latency (<150ms)

📋 TEST 6: PostgreSQL Extension Compatibility
   ⚠️  uuid-ossp: extension not supported
   ⚠️  pgcrypto: extension not supported

🧹 Cleaning up test table... OK

================================================================================
✅ ALL TESTS PASSED - CockroachDB Ready for Production
================================================================================
```

### If You See Errors:

**Error: "Permission denied"**
```bash
# Connect to CockroachDB Console (https://cockroachlabs.cloud/)
# Run in SQL shell:
GRANT CREATE ON DATABASE defaultdb TO modini;
GRANT ALL ON DATABASE defaultdb TO modini;
```

**Error: "Database does not exist"**
```bash
# In CockroachDB Console SQL shell:
CREATE DATABASE defaultdb;
GRANT ALL ON DATABASE defaultdb TO modini;
```

---

## **STEP 2: Apply Database Migrations** 🗄️

### Run the migration script:
```bash
./apply_migrations_cockroach.sh
```

### Expected Output:
```
================================================================================
CESAR ECOSYSTEM: CockroachDB Migration Runner
================================================================================

🔌 Testing CockroachDB connection...
✅ Connection successful

📋 Initializing migration tracker...
✅ Migration tracker ready

🚀 Applying migrations to CockroachDB...

📦 Processing: 001_phase_a_foundation
   Executing SQL...
   ✅ Applied successfully (2341ms)

📦 Processing: 002_routing_rules
   Executing SQL...
   ✅ Applied successfully (1523ms)

[... continues for all 11 migrations ...]

================================================================================
✅ MIGRATION COMPLETE
================================================================================

Summary:
  - Applied: 11
  - Skipped: 0
  - Failed:  0

Current Migration Status:
 migration_name                          | applied_at              | execution_time_ms | status
-----------------------------------------+-------------------------+-------------------+----------
 011_hippocampal_replay_tracking         | 2025-11-21 09:30:45    | 1234              | completed
 010_synthetic_organism_visualization    | 2025-11-21 09:30:43    | 2145              | completed
 ...
```

### If Migration Fails:

**Check which migrations succeeded:**
```bash
psql $COCKROACH_DB_URL -c "SELECT migration_name, status FROM schema_migrations ORDER BY applied_at;"
```

**Re-run failed migration manually:**
```bash
psql $COCKROACH_DB_URL -f migrations/XXX_failed_migration.sql
```

**Verify all tables created:**
```bash
psql $COCKROACH_DB_URL -c "\dt"
```

---

## **STEP 3: Initial Data Sync** 🔄

### Run the sync script:
```bash
./run_cockroach_sync.sh
```

### Expected Output:
```
================================================================================
CESAR ECOSYSTEM → COCKROACHDB SYNC
================================================================================

🔌 Connecting to local PostgreSQL...
✅ Connected to local database
🔌 Connecting to CockroachDB...
✅ Connected to CockroachDB

📋 Creating tables in CockroachDB...
✅ Tables created successfully

🤖 Syncing agents...
   Found 24 agents in local database
✅ Synced 24 agents to CockroachDB

🔍 Verifying sync...

✅ Total agents in CockroachDB: 24

📋 Sample agents with mob aliases:
   • Cesare_Sheppardini_CESAR       → Terry Delmonaco
   • Don_Vito_FinPsy                → Don Corleone
   • Paulie_Walnuts_MemoryKeeper    → Paulie Gualtieri
   • Bobby_Bacala_TaskMgr           → Bobby Baccalieri
   • Christopher_Moltisanti_Writer  → Christopher Moltisanti

================================================================================
🎉 SYNC COMPLETE!
================================================================================

Your 24 agents with mob aliases are now in CockroachDB Cloud!
```

### Verify Sync Manually:
```bash
# Check agent count
psql $COCKROACH_DB_URL -c "SELECT COUNT(*) FROM agents;"

# Check mob aliases
psql $COCKROACH_DB_URL -c "SELECT name, metadata->>'mob_alias' FROM agents LIMIT 5;"
```

---

## **STEP 4: Update API to Use CockroachDB** 🔌

### Critical Code Change Required:

**Edit file:** `api/main.py`

**Find this line (around line 25):**
```python
from database import get_db
```

**Replace with:**
```python
from api.database_v2 import get_db, init_database
```

**Add startup initialization (around line 180):**

Find:
```python
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting Multi-Agent Learning Ecosystem API v2.0")

    # Initialize async database connection pool
    try:
        await create_pool()
```

Add **BEFORE** `await create_pool()`:
```python
    # Initialize CockroachDB connection (NEW)
    try:
        from api.database_v2 import init_database
        init_database()
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
```

### Verify the change:
```bash
# Check imports
grep "database_v2" api/main.py

# Should see:
# from api.database_v2 import get_db, init_database
```

---

## **STEP 5: Run Integration Tests** 🧪

### Run the test suite:
```bash
python3 test_integration.py
```

### Expected Output:
```
================================================================================
CESAR ECOSYSTEM: INTEGRATION TEST SUITE
================================================================================

🧪 TEST: CockroachDB Connection
   ✅ PASS (145ms)

🧪 TEST: Local PostgreSQL Connection
   ✅ PASS (12ms)

🧪 TEST: Schema Exists
      All 6 tables present
   ✅ PASS (234ms)

🧪 TEST: Migration Tracking
      11 migrations applied
   ✅ PASS (123ms)

🧪 TEST: Agent Data Synced
      Local: 24 agents, CockroachDB: 24 agents
   ✅ PASS (178ms)

🧪 TEST: Mob Aliases Present
      24 agents with mob aliases
   ✅ PASS (156ms)

🧪 TEST: Data Consistency
      Agent 'Cesare_Sheppardini_CESAR' matches
   ✅ PASS (189ms)

🧪 TEST: Sync State Tracking
      Sync state has 6 entries
   ✅ PASS (134ms)

🧪 TEST: Read Performance
      Average latency: 143.45ms
   ✅ PASS (723ms)

🧪 TEST: Write Performance
      100 inserts: 3456ms (34.56ms/insert)
   ✅ PASS (3567ms)

================================================================================
TEST SUMMARY
================================================================================
Total:   10
✅ Passed: 10
❌ Failed: 0
⏭️  Skipped: 0
================================================================================
```

### Quick test mode (skip performance tests):
```bash
python3 test_integration.py --quick
```

---

## **STEP 6: Start the API and Verify** 🚀

### Start the API:
```bash
cd api
python3 main.py
```

### Expected Startup Output:
```
================================================================================
CESAR ECOSYSTEM DATABASE INITIALIZATION
================================================================================
🚀 PRODUCTION MODE: Connecting to CockroachDB Cluster
✅ Connected to COCKROACHDB
   Latency: 145.32ms
   Endpoint: cesar-ecosystem-10552.jxf.gcp-us-east1.cockroachlabs.cloud:26257/defaultdb
================================================================================

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
✅ Database pool initialized: {'status': 'healthy'}
✅ Redis connection established for rate limiting
✅ Redis Event Bus initialized
🎉 All systems initialized and ready!
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test the API:

**In a new terminal:**

```bash
# Health check
curl http://localhost:8000/health | jq

# Expected output:
{
  "status": "healthy",
  "timestamp": "2025-11-21T09:45:23.123456",
  "service": "multi-agent-learning-api",
  "version": "2.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "database": "cockroachdb",    # ← Should say "cockroachdb"
      "latency_ms": 145.32
    }
  }
}

# List agents
curl http://localhost:8000/api/agents | jq '.[0:3]'

# Expected: Array of 24 agents
```

---

## **STEP 7: Setup Bi-Directional Sync** 🔄

### Test the sync manually:
```bash
# Dry run (preview only)
python3 sync_bidirectional.py --dry-run

# Actual sync
python3 sync_bidirectional.py
```

### Expected Output:
```
================================================================================
CESAR ECOSYSTEM: BI-DIRECTIONAL DATABASE SYNC
================================================================================
Mode: LIVE
Direction: BOTH

🔌 Connecting to Local PostgreSQL...
✅ Connected
🔌 Connecting to CockroachDB...
✅ Connected

📦 Syncing table: agents
   ⬆️  Uploading changes to CockroachDB...
      Last sync: 2025-11-21 09:30:45
      Found 0 changed records
   ⬇️  Downloading changes from CockroachDB...
      Last sync: 2025-11-21 09:30:45
      Found 0 changed records

[... continues for all tables ...]

================================================================================
SYNCHRONIZATION COMPLETE
================================================================================
  ⬆️  Uploaded (Local → CockroachDB):   0
  ⬇️  Downloaded (CockroachDB → Local): 0
  ⚔️  Conflicts Resolved:               0
  ⏭️  Skipped (No Changes):             24
  ❌ Errors:                            0
================================================================================
```

### Setup Automatic Sync (Optional):

**Add to crontab:**
```bash
# Edit crontab
crontab -e

# Add this line (sync every 5 minutes):
*/5 * * * * cd "/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem" && python3 sync_bidirectional.py >> /var/log/cesar_sync.log 2>&1
```

---

## **STEP 8: Setup Frontend (Optional)** 🎨

### Run the frontend setup:
```bash
./setup_frontend.sh
```

### Expected Output:
```
================================================================================
🏗️  CESAR ECOSYSTEM: FRONTEND SCAFFOLD GENERATOR
================================================================================

📦 Creating Next.js application...
   Using: TypeScript, Tailwind CSS, ESLint, App Router

✔ What is your project named? … frontend
✔ Would you like to use TypeScript? … Yes
✔ Would you like to use ESLint? … Yes
✔ Would you like to use Tailwind CSS? … Yes
...

📦 Installing visualization dependencies...
+ lucide-react@0.294.0
+ recharts@2.10.3
+ framer-motion@10.16.16
...

📂 Creating component directories...
🔗 Creating API client...
✅ Found component source directory
   ✅ Copied DataBrainV6.tsx
   ✅ Copied MasterDashboard.tsx
   ...

================================================================================
✅ FRONTEND READY
================================================================================

Next Steps:
  1. cd frontend
  2. npm run dev
  3. Open http://localhost:3000
```

### Start the frontend:
```bash
cd frontend
npm run dev
```

**Open browser:** http://localhost:3000

---

## **STEP 9: Verification Checklist** ✅

Run through this checklist to ensure everything is working:

```bash
# 1. CockroachDB Connection
python3 test_cockroach_connection.py
# ✅ All tests pass

# 2. Migrations Applied
psql $COCKROACH_DB_URL -c "SELECT COUNT(*) FROM schema_migrations WHERE status='completed';"
# ✅ Should return: 11

# 3. Agents Synced
psql $COCKROACH_DB_URL -c "SELECT COUNT(*) FROM agents;"
# ✅ Should return: 24

# 4. API Using CockroachDB
curl http://localhost:8000/health | jq '.components.database.database'
# ✅ Should return: "cockroachdb"

# 5. Integration Tests Pass
python3 test_integration.py
# ✅ 10/10 tests pass

# 6. Mob Aliases Present
psql $COCKROACH_DB_URL -c "SELECT COUNT(*) FROM agents WHERE metadata->>'mob_alias' IS NOT NULL;"
# ✅ Should return: 24
```

---

## **STEP 10: Monitor and Maintain** 📊

### Check Sync Status:
```bash
psql $COCKROACH_DB_URL -c "SELECT * FROM sync_state ORDER BY last_sync_at DESC;"
```

### View API Logs:
```bash
# If running in terminal
# Logs appear in stdout

# If running as service
tail -f /var/log/cesar_api.log
```

### Monitor CockroachDB:
- **Console**: https://cockroachlabs.cloud/
- **Go to**: Your cluster → Metrics
- **Watch**: Query performance, storage usage, node health

---

## 🎯 **Success Criteria**

Your setup is complete when:

- ✅ `python3 test_cockroach_connection.py` → All tests pass
- ✅ `./apply_migrations_cockroach.sh` → 11 migrations applied
- ✅ `./run_cockroach_sync.sh` → 24 agents synced
- ✅ `curl http://localhost:8000/health` → Returns "cockroachdb"
- ✅ `python3 test_integration.py` → 10/10 tests pass
- ✅ Frontend loads at http://localhost:3000 (if setup)
- ✅ No errors in logs

---

## 🆘 **Troubleshooting**

### Issue: "Transaction aborted"
**Solution**: Already fixed in test script. Run `python3 test_cockroach_connection.py` again.

### Issue: "Permission denied"
```bash
# In CockroachDB Console SQL shell:
GRANT ALL ON DATABASE defaultdb TO modini;
```

### Issue: "Table already exists"
```bash
# Check migration status:
psql $COCKROACH_DB_URL -c "SELECT * FROM schema_migrations;"

# If migration shows failed, manually mark as completed:
psql $COCKROACH_DB_URL -c "UPDATE schema_migrations SET status='completed' WHERE migration_name='XXX';"
```

### Issue: "API still using local PostgreSQL"
```bash
# Verify import in api/main.py:
grep "database_v2" api/main.py

# Should see:
# from api.database_v2 import get_db, init_database

# Restart API:
# Ctrl+C in API terminal, then: python3 main.py
```

### Issue: "No agents synced"
```bash
# Check local database has agents:
psql postgresql://mcp_user:password@localhost:5432/mcp -c "SELECT COUNT(*) FROM agents;"

# If 0, you need to seed local database first
# If >0, re-run sync:
./run_cockroach_sync.sh
```

---

## 📚 **Additional Resources**

- **Complete Guide**: `COCKROACHDB_INTEGRATION_GUIDE.md`
- **Deployment Checklist**: `DEPLOYMENT_CHECKLIST.md`
- **API Documentation**: http://localhost:8000/docs (when API running)
- **CockroachDB Docs**: https://www.cockroachlabs.com/docs/

---

## 🎉 **You're Done!**

If all steps completed successfully, your CESAR ecosystem is now:

✅ Connected to CockroachDB Cloud
✅ Running with distributed SQL
✅ Syncing data automatically
✅ Production-ready

**Questions?** Review the troubleshooting section or check the comprehensive guides in the `docs/` directory.

---

**Last Updated**: November 21, 2025
**Version**: 2.0.0
