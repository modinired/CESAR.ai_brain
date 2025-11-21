# CONNECT YOUR SUPABASE PROJECT - QUICK GUIDE
**Your Supabase Org ID:** `mhvpvzmjvokzueyhcfoy`

---

## 🚀 QUICK SETUP (3 Steps - 5 Minutes)

### Step 1: Get Your Project Credentials

**Go to your Supabase project:**
1. Visit: https://supabase.com/dashboard/org/mhvpvzmjvokzueyhcfoy
2. Click on the project you want to use (or create new one)
3. Go to **Settings** → **API**
4. Copy these two values:

**You need:**
- ✅ **Project URL** (looks like: `https://xxxxx.supabase.co`)
- ✅ **anon/public key** (long string starting with `eyJ...`)

---

### Step 2: Add Credentials to CESAR

**Option A - Via Dashboard (Easiest):**
```bash
# Dashboard should already be running
# If not, launch it:
./launch_dashboard.sh

# Then:
# 1. Open dashboard
# 2. Click "☁️ Supabase Sync" tab
# 3. Click "⚙️ Configure Supabase" button
# 4. Paste your URL and key
# 5. Click "Save Configuration"
```

**Option B - Manual .env (Alternative):**
```bash
cd "/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem"

# Add these lines to .env:
echo "" >> .env
echo "# Supabase Configuration" >> .env
echo "SUPABASE_URL=https://YOUR-PROJECT-ID.supabase.co" >> .env
echo "SUPABASE_KEY=YOUR-ANON-KEY-HERE" >> .env

# Then reload dashboard
```

---

### Step 3: Create Tables in Supabase

**In your Supabase project:**
1. Go to **SQL Editor**
2. Click **New Query**
3. Copy and paste this SQL:

```sql
-- Create agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'idle',
    capabilities JSONB DEFAULT '[]',
    skills JSONB DEFAULT '[]',
    protocols JSONB DEFAULT '[]',
    config JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    tasks_completed INTEGER DEFAULT 0,
    tasks_failed INTEGER DEFAULT 0,
    success_rate NUMERIC(5,2) DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create a2a_messages table
CREATE TABLE IF NOT EXISTS a2a_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID,
    from_agent_id VARCHAR(255) NOT NULL,
    to_agent_id VARCHAR(255) NOT NULL,
    message_type VARCHAR(50),
    content TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create a2a_conversations table
CREATE TABLE IF NOT EXISTS a2a_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_type VARCHAR(100),
    participants JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create llm_collaborations table
CREATE TABLE IF NOT EXISTS llm_collaborations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    agent_id VARCHAR(255),
    prompt TEXT,
    local_model VARCHAR(100),
    cloud_model VARCHAR(100),
    local_response TEXT,
    cloud_response TEXT,
    selected_model VARCHAR(100),
    quality_score NUMERIC(3,2),
    cost NUMERIC(10,6),
    latency_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    agent_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) UNIQUE,
    agent_id VARCHAR(255),
    title VARCHAR(500),
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_agent_id ON agents(agent_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_a2a_messages_conversation ON a2a_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
```

4. Click **Run** (or press Cmd+Enter)
5. Verify tables appear in **Table Editor**

---

## ✅ TEST THE CONNECTION

### In CESAR Dashboard:

1. Go to "☁️ Supabase Sync" tab
2. Should show **"Connected ✅"** status (green)
3. Click **"🔄 Sync All Tables"** button
4. Wait ~5 seconds
5. All 6 tables should show "completed" status

### In Supabase Dashboard:

1. Go to **Table Editor**
2. Click on **agents** table
3. You should see **24 agents** with mob aliases like:
   - CESAR Sheppardini
   - Paulie Gualtieri
   - Silvio Dante
   - Moe Greene
   - etc.

---

## 🎯 EXPECTED RESULT

After sync completes, your Supabase project will have:

| Table | Records Synced |
|-------|---------------|
| agents | 24 |
| a2a_messages | 0 |
| a2a_conversations | 0 |
| llm_collaborations | 0 |
| sessions | 1 |
| tasks | 0 |

**Total: 25 records**

---

## 🔧 TROUBLESHOOTING

### "Connection Failed"
- Verify URL is correct (should end with `.supabase.co`)
- Verify you copied the **anon/public** key (not service_role key)
- Check for extra spaces when pasting

### "Table doesn't exist"
- Make sure you ran the SQL in Step 3
- Verify tables appear in Supabase Table Editor
- Table names must be lowercase

### "No data synced"
- Check CESAR dashboard shows 24 agents
- Verify Docker containers running: `docker ps`
- Check logs: `tail -f /tmp/supabase_sync.log`

---

## 📞 QUICK COMMANDS

```bash
# Launch dashboard
cd "/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem"
./launch_dashboard.sh

# Check local data ready to sync
docker exec multi_agent_postgres bash -c 'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT COUNT(*) FROM agents;"'

# Start automated sync scheduler (after manual test succeeds)
./launch_supabase_sync.sh &
tail -f /tmp/supabase_sync.log
```

---

## 🎓 NEXT STEPS AFTER CONNECTION

1. ✅ Verify 24 agents in Supabase
2. Create test workflow in dashboard
3. Set up real-time subscriptions (optional)
4. Configure automated daily sync
5. Add webhook endpoint for Supabase → CESAR triggers

---

**Your Org:** https://supabase.com/dashboard/org/mhvpvzmjvokzueyhcfoy
**Documentation:** SUPABASE_INTEGRATION_STATUS.md
**Support:** All infrastructure ready, just need credentials!

