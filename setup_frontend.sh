#!/bin/bash
#
# CESAR ECOSYSTEM: Frontend Scaffold Generator
# ============================================
# Creates Next.js application with pre-built dashboard components
#
# Components included:
# - MasterDashboard (Main console with sidebar navigation)
# - DataBrainV6 (3D knowledge graph visualization)
# - TalentMap (Organizational network physics)
# - LiquidityEngine (Financial flow simulation)
# - AutomationMatrix (Workflow particle system)
#
# Usage:
#   ./setup_frontend.sh

set -e

echo "================================================================================"
echo "🏗️  CESAR ECOSYSTEM: FRONTEND SCAFFOLD GENERATOR"
echo "================================================================================"
echo ""

# Check if frontend directory already exists
if [ -d "frontend" ]; then
    echo "⚠️  Warning: frontend/ directory already exists"
    read -p "   Delete and recreate? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "   Aborted."
        exit 1
    fi
    rm -rf frontend
fi

# 1. Create Next.js App (Non-interactive mode)
echo "📦 Creating Next.js application..."
echo "   Using: TypeScript, Tailwind CSS, ESLint, App Router"
echo ""

npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --use-npm \
  --no-git

cd frontend

# 2. Install UI Dependencies
echo ""
echo "📦 Installing visualization dependencies..."
npm install lucide-react recharts framer-motion clsx tailwind-merge

# Install WebSocket client
npm install ws
npm install --save-dev @types/ws

# 3. Create Directory Structure
echo ""
echo "📂 Creating component directories..."
mkdir -p src/components/dashboard
mkdir -p src/components/engines
mkdir -p src/lib

# 4. Create API Client Library
echo ""
echo "🔗 Creating API client..."
cat << 'EOF' > src/lib/api-client.ts
/**
 * CESAR API Client
 * Centralized HTTP client for FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class CESARApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // Agent endpoints
  async getAgents() {
    return this.request('/api/agents');
  }

  async getAgentSkills(agentId: string) {
    return this.request(`/api/agents/${agentId}/skills`);
  }

  // Workflow endpoints
  async getWorkflows() {
    return this.request('/api/workflows');
  }

  async triggerWorkflow(workflowName: string) {
    return this.request(`/api/workflows/trigger?workflow_name=${workflowName}`, {
      method: 'POST',
    });
  }

  // Stats endpoints
  async getSystemOverview() {
    return this.request('/api/stats/overview');
  }

  // Health check
  async health() {
    return this.request('/health');
  }
}

export const apiClient = new CESARApiClient();
EOF

# 5. Create WebSocket Hook
cat << 'EOF' > src/lib/useWebSocket.ts
/**
 * WebSocket Hook for Real-Time Updates
 */

import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export function useWebSocket(url: string) {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages((prev) => [message, ...prev].slice(0, 100)); // Keep last 100
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [url]);

  return { messages, isConnected };
}
EOF

# 6. Check if component source files exist
SOURCE_DIR="../cesar-ai-console"

if [ ! -d "$SOURCE_DIR" ]; then
    echo ""
    echo "⚠️  WARNING: Component source directory not found: $SOURCE_DIR"
    echo "   Creating placeholder components instead..."
    echo ""

    # Create placeholder components
    for component in DataBrainV6 AutomationMatrix LiquidityEngine TalentMap; do
        cat << EOF > "src/components/engines/${component}.tsx"
'use client';

import React from 'react';
import { Activity } from 'lucide-react';

export default function ${component}() {
  return (
    <div className="flex items-center justify-center h-full bg-slate-950 text-slate-500">
      <div className="text-center">
        <Activity className="w-12 h-12 mx-auto mb-4 text-emerald-500 animate-pulse" />
        <h2 className="text-xl font-bold text-white">${component} Loaded</h2>
        <p className="text-sm mt-2">Component implementation pending</p>
      </div>
    </div>
  );
}
EOF
    done

    # Create placeholder MasterDashboard
    cat << 'EOF' > src/components/dashboard/MasterDashboard.tsx
'use client';

import React, { useState } from 'react';
import { Cpu, Network, Zap, Users, TrendingUp, HeartPulse, Database } from 'lucide-react';

import DataBrainV6 from '../engines/DataBrainV6';
import AutomationMatrix from '../engines/AutomationMatrix';
import LiquidityEngine from '../engines/LiquidityEngine';
import TalentMap from '../engines/TalentMap';

export default function MasterDashboard() {
  const [activeTab, setActiveTab] = useState('overview');

  const renderContent = () => {
    switch(activeTab) {
      case 'brain': return <DataBrainV6 />;
      case 'workflows': return <AutomationMatrix />;
      case 'financial': return <LiquidityEngine />;
      case 'talent': return <TalentMap />;
      default: return (
        <div className="p-8">
          <h1 className="text-2xl font-bold text-white mb-4">CESAR.ai Command Center</h1>
          <p className="text-slate-400">Welcome to the multi-agent ecosystem dashboard.</p>
        </div>
      );
    }
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-200">
      <aside className="w-64 bg-slate-900 border-r border-slate-800 p-4">
        <div className="flex items-center gap-2 mb-8">
          <Cpu className="w-8 h-8 text-emerald-500" />
          <span className="text-xl font-bold">CESAR.ai</span>
        </div>

        <nav className="space-y-2">
          <button onClick={() => setActiveTab('overview')} className="w-full text-left px-3 py-2 rounded hover:bg-slate-800">Overview</button>
          <button onClick={() => setActiveTab('brain')} className="w-full text-left px-3 py-2 rounded hover:bg-slate-800">Data Brain</button>
          <button onClick={() => setActiveTab('workflows')} className="w-full text-left px-3 py-2 rounded hover:bg-slate-800">Workflows</button>
          <button onClick={() => setActiveTab('financial')} className="w-full text-left px-3 py-2 rounded hover:bg-slate-800">Financial</button>
          <button onClick={() => setActiveTab('talent')} className="w-full text-left px-3 py-2 rounded hover:bg-slate-800">Talent Map</button>
        </nav>
      </aside>

      <main className="flex-1 overflow-auto">
        {renderContent()}
      </main>
    </div>
  );
}
EOF

else
    echo "✅ Found component source directory"
    echo "   Copying engines..."

    # Copy actual component files if they exist
    for file in DataBrainV6.tsx AutomationMatrix.tsx LiquidityEngine.tsx TalentMap.tsx; do
        if [ -f "$SOURCE_DIR/$file" ]; then
            cp "$SOURCE_DIR/$file" "src/components/engines/"
            echo "   ✅ Copied $file"
        else
            echo "   ⚠️  $file not found in source"
        fi
    done

    if [ -f "$SOURCE_DIR/MasterDashboard.tsx" ]; then
        cp "$SOURCE_DIR/MasterDashboard.tsx" "src/components/dashboard/"
        echo "   ✅ Copied MasterDashboard.tsx"
    else
        echo "   ⚠️  MasterDashboard.tsx not found in source"
    fi
fi

# 7. Update Main Page
echo ""
echo "🔗 Wiring main page..."
cat << 'EOF' > src/app/page.tsx
import MasterDashboard from '@/components/dashboard/MasterDashboard';

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950">
      <MasterDashboard />
    </main>
  );
}
EOF

# 8. Create environment file
cat << 'EOF' > .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/events
EOF

# 9. Update package.json scripts
echo ""
echo "📝 Updating package.json scripts..."
npm pkg set scripts.dev="next dev"
npm pkg set scripts.build="next build"
npm pkg set scripts.start="next start"
npm pkg set scripts.lint="next lint"

echo ""
echo "================================================================================"
echo "✅ FRONTEND READY"
echo "================================================================================"
echo ""
echo "Directory Structure:"
echo "  frontend/"
echo "    ├── src/"
echo "    │   ├── app/                 # Next.js App Router pages"
echo "    │   ├── components/"
echo "    │   │   ├── dashboard/       # MasterDashboard"
echo "    │   │   └── engines/         # Visualization engines"
echo "    │   └── lib/                 # API client & utilities"
echo "    ├── .env.local               # Environment configuration"
echo "    └── package.json"
echo ""
echo "Next Steps:"
echo "  1. cd frontend"
echo "  2. npm run dev"
echo "  3. Open http://localhost:3000"
echo ""
echo "API Configuration:"
echo "  - Edit frontend/.env.local to change API endpoint"
echo "  - Default: http://localhost:8000"
echo ""
echo "================================================================================"
