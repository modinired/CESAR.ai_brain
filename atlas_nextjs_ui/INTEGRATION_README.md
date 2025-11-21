# Atlas Capital Automations - CESAR.ai Next.js UI

**Enterprise Multi-Agent Dashboard with AI-Powered Analytics**

*a Terry Dellmonaco Co.*

---

## Overview

This Next.js application provides a modern, AI-powered dashboard interface for the CESAR.ai multi-agent ecosystem. It integrates seamlessly with your existing Python backend and provides enhanced visualization, real-time monitoring, and AI-driven financial forecasting capabilities.

## CPU Slowdown Calibration

Your system has been automatically benchmarked and calibrated:

```
System: Darwin 25.1.0 (arm64)
CPU Count: 10 cores
Performance Ratio: 1.12x
Category: Standard Performance
Slowdown Multiplier: 2.0x
```

**What this means:**
- All AI inference timeouts are multiplied by 2.0x
- API request timeouts are adjusted for optimal performance
- Background task intervals are calibrated to prevent CPU overload

## Quick Start

### 1. Start the Application

```bash
cd "/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem"
./launch_atlas_nextjs_ui.sh
```

The dashboard will be available at: **http://localhost:9002**

### 2. Prerequisites

Ensure the following services are running:
- ✓ CESAR.ai API (http://localhost:8000)
- ✓ PostgreSQL Database
- ✓ Redis
- ✓ Docker containers

Check API status:
```bash
curl http://localhost:8000/health
```

## Features

### 🎯 Core Capabilities

1. **CESAR Agent Ecosystem Dashboard**
   - Real-time agent monitoring
   - Performance metrics
   - Task assignments
   - Agent collaboration visualization

2. **AI-Powered Financial Forecasting**
   - Scenario-based predictions
   - Key Performance Indicator (KPI) forecasting
   - Revenue, profit, and market share projections
   - Powered by Google Gemini 2.5 Flash

3. **Anomaly Detection System**
   - Real-time data anomaly identification
   - Pattern recognition
   - Automated alerts

4. **Workflow Management**
   - Visual workflow builder
   - Process automation
   - Task orchestration

5. **AI Chat Interface**
   - Natural language interactions
   - Context-aware responses
   - Multi-agent coordination

6. **Real-time Monitoring**
   - System health metrics
   - Performance dashboards
   - Connectivity status

## Architecture

### Technology Stack

- **Frontend**: Next.js 15.3.3 with React 18
- **UI Components**: Radix UI + Tailwind CSS
- **AI Integration**: Genkit with Google Gemini
- **Charts**: Recharts
- **Styling**: Tailwind CSS with custom animations

### Directory Structure

```
atlas_nextjs_ui/
├── src/
│   ├── app/                    # Next.js app router pages
│   │   ├── agents/            # Agent monitoring
│   │   ├── chat/              # AI chat interface
│   │   ├── forecasting/       # Financial forecasts
│   │   ├── anomalies/         # Anomaly detection
│   │   ├── workflows/         # Workflow management
│   │   └── terminal/          # Terminal interface
│   ├── components/            # React components
│   │   ├── ui/               # Base UI components
│   │   └── agents/           # Agent-specific components
│   ├── lib/                   # Utilities
│   │   ├── config.ts         # CPU calibration & configs
│   │   ├── types.ts          # TypeScript types
│   │   └── mock-data.ts      # Mock data
│   └── ai/                    # AI flows
│       └── flows/            # Genkit AI flows
│           ├── generate-financial-forecasts.ts
│           └── detect-anomalies-in-data.ts
├── .env                       # Environment configuration
└── tailwind.config.ts         # Tailwind configuration
```

## Configuration

### Environment Variables

Located in `.env`:

```env
# Gemini API Key (already configured)
GEMINI_API_KEY=AIzaSyDteOaTmK_8Vg-QOrQjh85bwQvogwTvV5o

# CESAR.ai Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# CPU Slowdown Multiplier
CPU_SLOWDOWN_MULTIPLIER=2.0

# Application Port
PORT=9002
```

### Timeout Configurations (lib/config.ts)

With 2.0x multiplier applied:
- AI Inference (short): 60s
- AI Inference (medium): 120s
- AI Inference (long): 240s
- API Requests: 10-60s
- Database Queries: 6-60s

## Integration with CESAR.ai Backend

The Next.js UI connects to your existing CESAR.ai API at `http://localhost:8000`.

### API Endpoints Used

```typescript
/health                              // System health check
/api/agents                          // Agent management
/api/chat                            // Chat interface
/api/forecasting                     // Financial forecasting
/api/anomalies                       // Anomaly detection
/api/workflows                       // Workflow management
/api/mcp/finpsy                      // Financial psychology analysis
```

## Development

### Install Dependencies

```bash
cd atlas_nextjs_ui
npm install
```

### Run Development Server

```bash
npm run dev
```

### Build for Production

```bash
npm run build
npm start
```

### Lint & Type Check

```bash
npm run lint
npm run typecheck
```

## Troubleshooting

### Issue: API Connection Failed

**Solution:**
```bash
# Check if API is running
curl http://localhost:8000/health

# Start Docker services if needed
cd "/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem"
docker-compose up -d
```

### Issue: Port 9002 Already in Use

**Solution:**
```bash
# Find process using port 9002
lsof -i :9002

# Kill the process or change port in .env
PORT=9003
```

### Issue: Slow Performance

The CPU slowdown multiplier (2.0x) is already calibrated for your system. If you experience slowness:

1. Check system resources:
```bash
top
```

2. Verify no other heavy processes are running
3. Consider increasing timeouts in `src/lib/config.ts`

## Production Deployment

### Using PM2

```bash
npm install -g pm2
pm2 start npm --name "atlas-nextjs-ui" -- start
pm2 save
pm2 startup
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 9002
CMD ["npm", "start"]
```

Build and run:
```bash
docker build -t atlas-nextjs-ui .
docker run -p 9002:9002 atlas-nextjs-ui
```

## Support & Documentation

- **CESAR.ai API Docs**: Check your existing documentation
- **Next.js Docs**: https://nextjs.org/docs
- **Genkit Docs**: https://firebase.google.com/docs/genkit

## License

Proprietary - Atlas Capital Automations, a Terry Dellmonaco Co.

---

**Built with Claude Code**
