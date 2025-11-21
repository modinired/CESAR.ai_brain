# CESAR Ecosystem: CockroachDB Integration Guide

## 📖 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [Component Reference](#component-reference)
4. [Data Flow Diagram](#data-flow-diagram)
5. [Deployment Guide](#deployment-guide)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     CESAR ECOSYSTEM                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │   Next.js    │      │   FastAPI    │      │ CockroachDB  │ │
│  │  Dashboard   │◄────►│   Backend    │◄────►│   Cluster    │ │
│  │  (Frontend)  │      │   (API)      │      │  (Cloud DB)  │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
│         │                      │                      │         │
│         │                      │                      │         │
│         │                      ▼                      │         │
│         │              ┌──────────────┐              │         │
│         └─────────────►│  PostgreSQL  │◄─────────────┘         │
│                        │    (Local)   │                        │
│                        └──────────────┘                        │
│                                │                                │
│                                ▼                                │
│                        ┌──────────────┐                        │
│                        │ Bi-Directional │                      │
│                        │  Sync Service  │                      │
│                        └──────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

- **Hybrid Architecture**: Local PostgreSQL for speed, CockroachDB for durability
- **Bi-Directional Sync**: Automatic conflict resolution
- **High Availability**: 99.99% uptime with distributed SQL
- **Real-Time Updates**: WebSocket broadcasting for live dashboards

---

## 🚀 Quick Start

### Prerequisites

```bash
# Required software
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (local)
- CockroachDB Cloud account
```

### Initial Setup (5 Minutes)

```bash
# 1. Navigate to project
cd "/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem"

# 2. Test CockroachDB connection
python3 test_cockroach_connection.py

# 3. Apply schema migrations
./apply_migrations_cockroach.sh

# 4. Initial data sync
./run_cockroach_sync.sh

# 5. Start API (now uses CockroachDB)
cd api
python3 main.py

# 6. Setup frontend (optional)
cd ..
./setup_frontend.sh
cd frontend && npm run dev
```

### Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Check database connection
python3 -c "from api.database_v2 import check_database_connection; print(check_database_connection())"

# View synced agents
psql $COCKROACH_DB_URL -c "SELECT count(*) FROM agents;"
```

---

## 🔧 Component Reference

### 1. Database Connection Layer

**File**: `api/database_v2.py`

**Priority Logic**:
```python
# Production/Staging: Always use CockroachDB
if ENVIRONMENT in ['production', 'staging']:
    use_cockroach = True

# Development: Use local for speed (override with ENVIRONMENT=staging)
else:
    use_cockroach = False (default to local PostgreSQL)
```

**Environment Variables**:
```bash
# .env.cockroach
COCKROACH_DB_URL=postgresql://user:password@host:26257/defaultdb?sslmode=verify-full

# .env
ENVIRONMENT=production  # or 'staging', 'development'
```

**Usage in API**:
```python
from api.database_v2 import get_db, check_database_connection

# In FastAPI route
@app.get("/api/agents")
async def list_agents(db: Session = Depends(get_db)):
    agents = db.query(Agent).all()
    return agents
```

---

### 2. Migration Runner

**File**: `apply_migrations_cockroach.sh`

**Features**:
- ✅ Idempotent execution (safe to run multiple times)
- ✅ Tracking table for applied migrations
- ✅ Dry-run mode
- ✅ Error recovery

**Usage**:
```bash
# Normal execution
./apply_migrations_cockroach.sh

# Preview without applying
./apply_migrations_cockroach.sh --dry-run

# Check status
psql $COCKROACH_DB_URL -c "SELECT * FROM schema_migrations ORDER BY applied_at DESC;"
```

**Migration Order** (Critical - Do Not Change):
```
001_phase_a_foundation.sql              # Core tables
002_routing_rules.sql                   # Agent routing
003_phase_b_cognitive_memory.sql        # Memory system
004_phase_c_knowledge_graph.sql         # Graph structures
005_phase_d_attention_coordination.sql  # Coordination
006_phase_e_continual_learning.sql      # Learning loops
007_local_llm_integration.sql           # LLM support
008_a2a_protocol_and_llm_collaboration.sql  # A2A messaging
009_supabase_integration.sql            # Real-time layer
010_synthetic_organism_visualization.sql # Viz tables
011_hippocampal_replay_tracking.sql     # Replay system
```

---

### 3. Bi-Directional Sync

**File**: `sync_bidirectional.py`

**Conflict Resolution Strategy**:
- Uses `updated_at` timestamp (winner = most recent)
- Logs conflicts to `sync_state` table
- Skips unchanged records (incremental sync)

**Usage**:
```bash
# Normal sync (both directions)
python3 sync_bidirectional.py

# Preview changes
python3 sync_bidirectional.py --dry-run

# Sync specific table
python3 sync_bidirectional.py --table=agents

# One-way sync
python3 sync_bidirectional.py --direction=up    # Local → CockroachDB
python3 sync_bidirectional.py --direction=down  # CockroachDB → Local
```

**Scheduling** (Recommended for Production):
```bash
# Add to crontab (sync every 5 minutes)
*/5 * * * * cd /path/to/cesar_ecosystem && python3 sync_bidirectional.py >> /var/log/cesar_sync.log 2>&1
```

---

### 4. Frontend Dashboard

**File**: `setup_frontend.sh`

**Components**:
- `MasterDashboard.tsx` - Main navigation & layout
- `DataBrainV6.tsx` - 3D knowledge graph (physics-based)
- `TalentMap.tsx` - Organizational network analysis
- `LiquidityEngine.tsx` - Financial flow simulation
- `AutomationMatrix.tsx` - Workflow visualization

**Setup**:
```bash
./setup_frontend.sh
cd frontend
npm run dev  # Access at http://localhost:3000
```

**API Integration**:
```typescript
// frontend/src/lib/api-client.ts
import { apiClient } from '@/lib/api-client';

// Fetch agents
const agents = await apiClient.getAgents();

// WebSocket connection
const { messages, isConnected } = useWebSocket('ws://localhost:8000/ws/events');
```

---

## 📊 Data Flow Diagram

### Normal Operation

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Agent     │──────►│  Local DB   │──────►│ CockroachDB │
│  Actions    │       │ (Fast Write)│       │(Durability) │
└─────────────┘       └─────────────┘       └─────────────┘
                             │                      │
                             │    Bi-Directional    │
                             │    Sync (Every 5m)   │
                             │◄─────────────────────┘
                             │
                             ▼
                      ┌─────────────┐
                      │  FastAPI    │
                      │  (Reads)    │
                      └─────────────┘
                             │
                             ▼
                      ┌─────────────┐
                      │  Frontend   │
                      │ Dashboard   │
                      └─────────────┘
```

### Disaster Recovery

```
┌─────────────┐
│  Local DB   │──────► FAILURE
│  CORRUPTED  │
└─────────────┘
       │
       │  Full Restore
       ▼
┌─────────────┐
│ CockroachDB │──────► Restore all data
│  (SOURCE)   │
└─────────────┘
       │
       ▼
┌─────────────┐
│  New Local  │──────► Resume operations
│  Instance   │
└─────────────┘
```

---

## 🚢 Deployment Guide

### Development Environment

```bash
export ENVIRONMENT=development
# Uses local PostgreSQL by default
# Sync to CockroachDB manually: ./run_cockroach_sync.sh
```

### Staging Environment

```bash
export ENVIRONMENT=staging
# Forced CockroachDB connection
# Continuous sync enabled
```

### Production Environment

```bash
export ENVIRONMENT=production
# CockroachDB only (no local fallback)
# Automated sync every 5 minutes
# Monitoring enabled (Prometheus)
```

### Docker Deployment

```yaml
# docker-compose.yml (excerpt)
services:
  api:
    environment:
      - ENVIRONMENT=production
      - COCKROACH_DB_URL=${COCKROACH_DB_URL}
    command: uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🔍 Troubleshooting

### Issue: "Connection Refused"

**Symptoms**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
1. Check IP allowlist in CockroachDB Console
2. Verify port 26257 is not blocked
3. Test with: `telnet <host> 26257`

---

### Issue: "SSL Certificate Verify Failed"

**Symptoms**: `SSL error: certificate verify failed`

**Solutions**:
```bash
# Option 1: Use verify-ca mode (less strict)
COCKROACH_DB_URL="...?sslmode=verify-ca"

# Option 2: Download root certificate
curl -o root.crt https://cockroachlabs.cloud/clusters/<cluster-id>/cert
# Update connection string to point to cert
```

---

### Issue: "Migration Already Applied"

**Symptoms**: Table already exists errors

**Solution**:
```bash
# Check migration status
psql $COCKROACH_DB_URL -c "SELECT * FROM schema_migrations;"

# Reset specific migration (DANGEROUS)
psql $COCKROACH_DB_URL -c "DELETE FROM schema_migrations WHERE migration_name = '008_a2a_protocol';"

# Re-run
./apply_migrations_cockroach.sh
```

---

### Issue: "Sync Conflicts"

**Symptoms**: Records not syncing or duplicate data

**Solution**:
```bash
# Check sync state
psql $COCKROACH_DB_URL -c "SELECT * FROM sync_state;"

# Force full re-sync
psql $COCKROACH_DB_URL -c "DELETE FROM sync_state;"
python3 sync_bidirectional.py
```

---

## ❓ FAQ

### Q: Should I use local PostgreSQL or CockroachDB in development?

**A**: Use **local PostgreSQL** for development speed. CockroachDB adds ~100ms latency due to cloud roundtrip. Set `ENVIRONMENT=development` (default).

Use CockroachDB in development only when testing:
- Multi-region scenarios
- Distributed transactions
- Production-like performance

---

### Q: How often does sync run?

**A**: Manual sync (`./run_cockroach_sync.sh`) runs on-demand.

For automatic sync:
- Development: Manual only
- Staging: Every 5 minutes (cron)
- Production: Every 5 minutes (cron) + immediate on critical tables

---

### Q: What happens if CockroachDB is down?

**A**:
- API continues using local PostgreSQL
- Sync service logs error and retries
- Data accumulates locally
- When CockroachDB recovers, sync resumes automatically

---

### Q: Can I use Supabase instead of CockroachDB?

**A**: Yes, but requires modifications:
1. Update connection string in `.env.cockroach`
2. Replace `apply_migrations_cockroach.sh` logic for Supabase
3. Migration 009 (`supabase_integration.sql`) has Supabase-specific features

---

### Q: How do I monitor sync health?

**A**:
```bash
# Check last sync time
psql $COCKROACH_DB_URL -c "SELECT * FROM sync_state ORDER BY last_sync_at DESC;"

# Check for errors
tail -f /var/log/cesar_sync.log

# Prometheus metrics (if enabled)
curl http://localhost:8000/metrics | grep sync_
```

---

## 📞 Support

- **Documentation**: `/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem/docs/`
- **Logs**: `/var/log/cesar_*.log`
- **Health Check**: `http://localhost:8000/health`

---

**Last Updated**: November 21, 2025
**Version**: 2.0.0
**Maintained By**: CESAR Development Team
