# 🎨 Frontend Setup Guide - Atlas Next.js UI

**Date:** November 21, 2025
**Status:** Ready for Development

---

## 📋 PREREQUISITES

- Node.js 18+ installed
- npm or yarn package manager
- Backend API running on port 8011
- CockroachDB with seeded data

---

## 🚀 INITIAL SETUP

### Step 1: Install Dependencies

```bash
cd atlas_nextjs_ui

# Install main dependencies
npm install

# Install ESLint (required for linting)
npm install --save-dev eslint eslint-config-next

# Optional: Install additional dev tools
npm install --save-dev prettier
```

**Note:** ESLint config (`.eslintrc.json`) is already created, but ESLint itself needs to be installed locally.

---

### Step 2: Configure Environment

Create `.env.local` file:

```bash
cat > .env.local << 'EOF'
# Backend API base URL (required)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8011

# WebSocket for real-time telemetry (optional)
NEXT_PUBLIC_WS_TELEMETRY=ws://localhost:8011/ws/telemetry

# API key for protected routes (optional - swap, events)
# Get this from: python scripts/seed_anonymized.py
NEXT_PUBLIC_API_KEY=ak_admin_xxxxxxxxxxxxxxxx
EOF
```

**Environment Variables Explained:**

| Variable | Required | Purpose | Example |
|----------|----------|---------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | ✅ Yes | Backend API endpoint | `http://localhost:8011` |
| `NEXT_PUBLIC_WS_TELEMETRY` | ❌ No | WebSocket for live updates | `ws://localhost:8011/ws/telemetry` |
| `NEXT_PUBLIC_API_KEY` | ⚠️ Optional | Auth for swap/events | `ak_admin_...` |

---

### Step 3: Verify Backend is Running

```bash
# Check backend health
curl http://localhost:8011/health

# Expected response:
# {"status":"healthy","version":"2.0","timestamp":"..."}

# Verify knowledge endpoints
curl http://localhost:8011/atlas/knowledge/daily-summary | jq

# Verify workflow endpoints
curl http://localhost:8011/atlas/automation/workflows | jq
```

---

## 🏃 RUNNING THE APPLICATION

### Development Mode

```bash
# Start development server on port 9003
npm run dev -- --port 9003

# Or use default port 3000
npm run dev

# Output:
# ▲ Next.js 14.x.x
# - Local:        http://localhost:9003
# - Ready in 2.5s
```

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start

# Or specify port
npm start -- --port 9003
```

---

## 🧪 LINTING & CODE QUALITY

### ESLint Configuration

A minimal ESLint config is already created at `.eslintrc.json`:

```json
{
  "extends": "next/core-web-vitals",
  "rules": {
    "react/no-unescaped-entities": "off",
    "@next/next/no-img-element": "off"
  }
}
```

### Running Linter

```bash
# Run ESLint (after installing)
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix

# Check specific files
npm run lint -- src/app/agents/page.tsx
```

**Note:** If linting fails, ensure ESLint is installed:
```bash
npm install --save-dev eslint eslint-config-next
```

---

## 📁 PROJECT STRUCTURE

```
atlas_nextjs_ui/
│
├── src/
│   ├── app/                      # Next.js 14 App Router
│   │   ├── agents/               # Agents page (cognition scores)
│   │   ├── workflows/            # Workflows page (matrix + events)
│   │   ├── optic/                # Optic Nerve page (vision upload)
│   │   ├── databrain/            # DataBrain page (sync)
│   │   ├── chat/                 # Chat interface
│   │   ├── terminal/             # Terminal interface
│   │   ├── agent-forge/          # Agent creation wizard
│   │   ├── forecasting/          # Financial forecasts
│   │   ├── anomalies/            # Anomaly detection
│   │   └── singularity-console/  # Advanced terminal
│   │
│   ├── components/               # React components
│   │   ├── agents/               # Agent-related components
│   │   ├── dashboard/            # Dashboard widgets
│   │   ├── forecasting/          # Forecasting components
│   │   ├── anomalies/            # Anomaly components
│   │   ├── console/              # Console components
│   │   ├── layout/               # Layout components
│   │   ├── icons/                # Icon components
│   │   └── ui/                   # shadcn/ui components
│   │
│   ├── hooks/                    # Custom React hooks
│   │   ├── use-mobile.tsx        # Mobile detection
│   │   └── use-toast.ts          # Toast notifications
│   │
│   └── ai/                       # Genkit AI integration
│       ├── genkit.ts             # Genkit setup
│       ├── dev.ts                # Dev server
│       └── flows/                # AI flows
│
├── public/                       # Static assets
│   └── branding/                 # Brand assets
│
├── .env.local                    # Environment variables (create this)
├── .eslintrc.json                # ESLint config
├── next.config.ts                # Next.js config
├── tailwind.config.ts            # Tailwind CSS config
├── tsconfig.json                 # TypeScript config
├── package.json                  # Dependencies
└── README.md                     # Project README
```

---

## 🔌 API INTEGRATION

### Pages and Their Endpoints

| Page | Endpoints Used | Features |
|------|----------------|----------|
| `/agents` | `GET /api/agents`<br>`GET /atlas/agents/{id}/cognition` | Live cognition scores, health indicators |
| `/workflows` | `GET /atlas/automation/workflows`<br>`GET /atlas/automation/matrix/{id}`<br>`GET /atlas/automation/matrix/{id}/events`<br>`POST /atlas/automation/matrix/swap` | Dynamic workflows, events timeline, swap actions |
| `/optic` | `GET /atlas/senses/optic/jobs`<br>`POST /atlas/senses/optic/upload`<br>`GET /atlas/senses/optic/job/{id}` | Recent jobs, upload, status polling |
| `/databrain` | `POST /databrain/sync`<br>`GET /databrain/status` | Sync trigger, status monitoring |

---

## 🎨 STYLING

### Tailwind CSS

Tailwind is pre-configured with custom theme:

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        // ... shadcn/ui color system
      }
    }
  }
}
```

### shadcn/ui Components

Pre-installed components in `src/components/ui/`:
- Button, Card, Dialog, Dropdown Menu
- Input, Label, Select, Textarea
- Table, Tabs, Toast, Tooltip
- Alert, Badge, Progress, Skeleton
- And 20+ more...

Usage:
```typescript
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

<Card>
  <Button variant="default">Click Me</Button>
</Card>
```

---

## 🔐 AUTHENTICATION & SECURITY

### API Key Usage

Protected routes require `X-API-Key` header:

```typescript
// Workflow swap action
const response = await fetch('/atlas/automation/matrix/swap', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.NEXT_PUBLIC_API_KEY
  },
  body: JSON.stringify({
    workflow_id: 'wf-01',
    step_a: 'data_collection',
    step_b: 'analysis'
  })
});
```

### Environment Variable Security

- ✅ `.env.local` is gitignored
- ✅ `NEXT_PUBLIC_*` variables are safe for browser
- ✅ API keys are optional for read operations
- ⚠️ Only use admin key for development

---

## 🐛 TROUBLESHOOTING

### Common Issues

**1. "Cannot connect to backend"**
```bash
# Check if backend is running
curl http://localhost:8011/health

# Check environment variable
echo $NEXT_PUBLIC_API_BASE_URL

# Verify .env.local exists
cat .env.local
```

**2. "Module not found" errors**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**3. "ESLint not found"**
```bash
# Install ESLint
npm install --save-dev eslint eslint-config-next

# Verify installation
npx eslint --version
```

**4. "Port 9003 already in use"**
```bash
# Find process using port
lsof -ti:9003

# Kill process
lsof -ti:9003 | xargs kill -9

# Or use different port
npm run dev -- --port 3000
```

**5. "Cognition scores not loading"**
```bash
# Verify agents exist in database
curl http://localhost:8011/api/agents | jq

# Check cognition endpoint
curl http://localhost:8011/atlas/agents/portfolio_optimizer/cognition | jq

# Verify seed data loaded
psql "$COCKROACH_DB_URL" -c "SELECT COUNT(*) FROM agents;"
```

---

## 📊 PERFORMANCE OPTIMIZATION

### Recommended Settings

**1. Next.js Config** (`next.config.ts`):
```typescript
const config = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['localhost'],
  },
  experimental: {
    optimizePackageImports: ['@/components/ui'],
  },
}
```

**2. TypeScript Config** (`tsconfig.json`):
```json
{
  "compilerOptions": {
    "incremental": true,
    "skipLibCheck": true
  }
}
```

**3. Build Optimization**:
```bash
# Analyze bundle size
npm run build
npx @next/bundle-analyzer
```

---

## 🧪 TESTING

### Manual Testing Checklist

```bash
# Start backend and frontend
cd api && uvicorn main:app --port 8011 --reload &
cd atlas_nextjs_ui && npm run dev -- --port 9003 &

# Visit pages:
open http://localhost:9003/agents
open http://localhost:9003/workflows
open http://localhost:9003/optic
open http://localhost:9003/databrain

# Test features:
# - Agents: Check cognition scores load
# - Workflows: Select workflow, view events
# - Optic: Upload file, watch status
# - DataBrain: Trigger sync
```

---

## 📦 DEPLOYMENT

### Production Build

```bash
# Build for production
npm run build

# Output will be in .next/ directory
# Deploy to Vercel, Netlify, or your hosting platform
```

### Environment Variables for Production

Set these in your hosting platform:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.com
NEXT_PUBLIC_WS_TELEMETRY=wss://your-api-domain.com/ws/telemetry
NEXT_PUBLIC_API_KEY=ak_production_key_here
```

### Vercel Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
# https://vercel.com/your-project/settings/environment-variables
```

---

## 🔄 UPDATES & MAINTENANCE

### Updating Dependencies

```bash
# Check for outdated packages
npm outdated

# Update all dependencies
npm update

# Update Next.js specifically
npm install next@latest react@latest react-dom@latest
```

### Keeping Sync with Backend

When backend API changes:

1. Update API calls in page files
2. Update TypeScript types if needed
3. Test all affected pages
4. Update this documentation

---

## 📚 ADDITIONAL RESOURCES

### Documentation:
- **Next.js**: https://nextjs.org/docs
- **React**: https://react.dev
- **Tailwind CSS**: https://tailwindcss.com/docs
- **shadcn/ui**: https://ui.shadcn.com

### Internal Docs:
- **DYNAMIC_UI_INTEGRATION.md** - API integration guide
- **OPERATIONAL_STATUS.md** - System status
- **LIVING_BRAIN_ACTIVATED.md** - Activation report

---

## ✅ SETUP CHECKLIST

- [ ] Node.js 18+ installed
- [ ] Backend running on port 8011
- [ ] Database seeded with demo data
- [ ] Dependencies installed (`npm install`)
- [ ] ESLint installed (`npm install --save-dev eslint`)
- [ ] `.env.local` created with API base URL
- [ ] API key added (optional)
- [ ] Development server starts without errors
- [ ] Agents page loads with cognition scores
- [ ] Workflows page displays matrices and events
- [ ] Optic page shows recent jobs and allows upload
- [ ] DataBrain page can trigger sync

---

## 🎯 QUICK START COMMAND

```bash
# Complete setup in one go
cd atlas_nextjs_ui && \
npm install && \
npm install --save-dev eslint eslint-config-next && \
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_BASE_URL=http://localhost:8011
NEXT_PUBLIC_WS_TELEMETRY=ws://localhost:8011/ws/telemetry
NEXT_PUBLIC_API_KEY=YOUR_API_KEY_HERE
EOF
npm run dev -- --port 9003
```

---

**Status: ✅ READY FOR DEVELOPMENT**
**All dependencies documented**
**Complete setup workflow provided**

Built by Claude & Terry
November 21, 2025

🎨 **Beautiful UI, powerful brain, seamless integration.**
