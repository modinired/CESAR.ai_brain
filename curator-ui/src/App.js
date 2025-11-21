import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import ChatInterface from "./components/ChatInterface";
import WorkflowList from "./components/WorkflowList";
import MaterialDetail from "./components/MaterialDetail";
import MaterialList from "./components/MaterialList";
import ReflectionList from "./components/ReflectionList";
import AgentDashboard from "./components/AgentDashboard";
import SystemOverview from "./components/SystemOverview";
import AgentActivityFeed from "./components/AgentActivityFeed";

const brandingImages = [
  { src: "/branding/aca_logo.png", alt: "Atlas Capital Automations" },
  { src: "/branding/cesar_glow.png", alt: "CESAR glowing circuit" },
  { src: "/branding/cesar_robots.png", alt: "CESAR and robots" },
  { src: "/branding/golden_robot.png", alt: "Golden guardian" },
  { src: "/branding/terry_neon.png", alt: "Terry Dellmonaco neon" },
];

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-950">
        {/* Navigation */}
        <nav className="bg-slate-900/80 backdrop-blur border-b border-slate-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center space-x-3">
                <img
                  src="/branding/aca_logo_alt.png"
                  alt="Atlas Capital Automations"
                  className="h-10 w-auto"
                />
                <div>
                  <h1 className="text-xl font-bold text-white tracking-wide">
                    CESAR · Symbiotic Recursive Cognition Agent Ecosystem
                  </h1>
                  <p className="text-xs text-slate-300 uppercase tracking-widest">
                    Terry Dellmonaco MCP · Atlas Capital Automations
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-1">
                <Link
                  to="/chat"
                  className="text-slate-200 hover:text-cyan-400 px-3 py-2 rounded-md text-sm font-medium"
                >
                  💬 Chat
                </Link>
                <Link
                  to="/"
                  className="text-slate-200 hover:text-cyan-400 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Overview
                </Link>
                <Link
                  to="/agents"
                  className="text-slate-200 hover:text-cyan-400 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Agents
                </Link>
                <Link
                  to="/workflows"
                  className="text-slate-200 hover:text-cyan-400 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Workflows
                </Link>
                <Link
                  to="/materials"
                  className="text-slate-200 hover:text-cyan-400 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Materials
                </Link>
                <Link
                  to="/reflections"
                  className="text-slate-200 hover:text-cyan-400 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Reflections
                </Link>
                <Link
                  to="/activity"
                  className="text-slate-200 hover:text-cyan-400 px-3 py-2 rounded-md text-sm font-medium"
                >
                  🔴 Live Activity
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Branding strip */}
        <div className="bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-purple-500/10 border-b border-slate-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {brandingImages.map((image) => (
                <div
                  key={image.alt}
                  className="bg-slate-900/70 rounded-xl border border-slate-800 p-3 flex items-center justify-center"
                >
                  <img
                    src={image.src}
                    alt={image.alt}
                    className="h-20 object-contain drop-shadow-lg"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/chat" element={<ChatInterface />} />
            <Route path="/" element={<SystemOverview />} />
            <Route path="/materials" element={<MaterialList />} />
            <Route path="/material/:id" element={<MaterialDetail />} />
            <Route path="/reflections" element={<ReflectionList />} />
            <Route path="/agents" element={<AgentDashboard />} />
            <Route path="/workflows" element={<WorkflowList />} />
            <Route path="/activity" element={<div className="h-[calc(100vh-300px)]"><AgentActivityFeed /></div>} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-slate-900/80 border-t border-slate-800 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <p className="text-center text-slate-300 text-sm tracking-wide">
              CESAR · Atlas Capital Automations · Terry Dellmonaco MCP
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
