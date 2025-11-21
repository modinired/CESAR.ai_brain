/**
 * Agent Activity Feed - Real-Time Event Display
 * ==============================================
 *
 * PhD-Level Implementation: Real-Time Dashboard Component
 * Based on CESAR.ai PhD Enhancement Framework
 *
 * Features:
 * - Live WebSocket event streaming
 * - Event type filtering
 * - Agent-specific filtering
 * - Connection status indicator
 * - Latency monitoring
 * - Auto-scroll with manual override
 *
 * Usage:
 * ```jsx
 * import AgentActivityFeed from './components/AgentActivityFeed';
 *
 * function Dashboard() {
 *   return <AgentActivityFeed />;
 * }
 * ```
 */

import React, { useState, useEffect, useRef } from 'react';
import useWebSocket from '../hooks/useWebSocket';

const EVENT_COLORS = {
  agent_status: 'bg-blue-100 border-blue-400 text-blue-900',
  agent_task: 'bg-green-100 border-green-400 text-green-900',
  agent_metric: 'bg-purple-100 border-purple-400 text-purple-900',
  workflow_update: 'bg-yellow-100 border-yellow-400 text-yellow-900',
  workflow_step: 'bg-orange-100 border-orange-400 text-orange-900',
  learning: 'bg-indigo-100 border-indigo-400 text-indigo-900',
  memory_consolidation: 'bg-pink-100 border-pink-400 text-pink-900',
  system_alert: 'bg-red-100 border-red-400 text-red-900',
  system_metric: 'bg-gray-100 border-gray-400 text-gray-900',
  collaboration_request: 'bg-teal-100 border-teal-400 text-teal-900',
  collaboration_response: 'bg-cyan-100 border-cyan-400 text-cyan-900',
  default: 'bg-gray-50 border-gray-300 text-gray-800'
};

const EVENT_ICONS = {
  agent_status: '🤖',
  agent_task: '⚙️',
  agent_metric: '📊',
  workflow_update: '🔄',
  workflow_step: '👣',
  learning: '🧠',
  memory_consolidation: '💾',
  system_alert: '⚠️',
  system_metric: '📈',
  collaboration_request: '🤝',
  collaboration_response: '✅',
  default: '📡'
};

function AgentActivityFeed() {
  // State
  const [filter, setFilter] = useState('all');
  const [agentFilter, setAgentFilter] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const [displayedEvents, setDisplayedEvents] = useState([]);

  // Refs
  const feedRef = useRef(null);
  const lastScrollTop = useRef(0);

  // WebSocket connection
  const {
    isConnected,
    connectionState,
    events,
    latency,
    clearEvents,
    subscribe,
    unsubscribe
  } = useWebSocket({
    url: `ws://${window.location.hostname}:8000/ws/events`,
    rooms: ['all'],
    onEvent: (event) => {
      console.log('[AgentActivityFeed] New event:', event);
    }
  });

  // Filter events based on selected filters
  useEffect(() => {
    let filtered = events;

    // Filter by event type
    if (filter !== 'all') {
      filtered = filtered.filter(event => event.type === filter);
    }

    // Filter by agent ID
    if (agentFilter.trim() !== '') {
      const searchLower = agentFilter.toLowerCase();
      filtered = filtered.filter(event => {
        const agentId = event.data?.agent_id || '';
        return agentId.toLowerCase().includes(searchLower);
      });
    }

    setDisplayedEvents(filtered);
  }, [events, filter, agentFilter]);

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (autoScroll && feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [displayedEvents, autoScroll]);

  // Detect manual scroll to disable auto-scroll
  const handleScroll = () => {
    if (!feedRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = feedRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;

    // If user scrolls up, disable auto-scroll
    if (scrollTop < lastScrollTop.current) {
      setAutoScroll(false);
    }

    // If user scrolls to bottom, enable auto-scroll
    if (isAtBottom) {
      setAutoScroll(true);
    }

    lastScrollTop.current = scrollTop;
  };

  // Get unique event types for filter dropdown
  const eventTypes = ['all', ...new Set(events.map(e => e.type))];

  // Connection status indicator
  const connectionStatus = () => {
    switch (connectionState) {
      case 'connected':
        return (
          <span className="flex items-center text-green-600">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
            Connected
            {latency !== null && (
              <span className="ml-2 text-xs text-gray-500">
                ({latency}ms)
              </span>
            )}
          </span>
        );
      case 'connecting':
        return (
          <span className="flex items-center text-yellow-600">
            <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
            Connecting...
          </span>
        );
      case 'error':
        return (
          <span className="flex items-center text-red-600">
            <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
            Error
          </span>
        );
      default:
        return (
          <span className="flex items-center text-gray-600">
            <span className="w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
            Disconnected
          </span>
        );
    }
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  // Render event content based on type
  const renderEventContent = (event) => {
    const { type, data } = event;

    switch (type) {
      case 'agent_status':
        return (
          <div>
            <span className="font-semibold">{data.agent_id}</span>
            <span className="mx-2">→</span>
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              data.status === 'active' ? 'bg-green-200' :
              data.status === 'error' ? 'bg-red-200' :
              'bg-gray-200'
            }`}>
              {data.status}
            </span>
            {data.message && (
              <p className="text-sm mt-1 text-gray-600">{data.message}</p>
            )}
          </div>
        );

      case 'agent_task':
        return (
          <div>
            <span className="font-semibold">{data.agent_id}</span>
            <span className="mx-2">{data.action === 'start' ? '▶️' : '✓'}</span>
            <span className="text-sm">{data.task_type || data.task_id}</span>
            {data.description && (
              <p className="text-sm mt-1 text-gray-600">{data.description}</p>
            )}
            {data.error && (
              <p className="text-sm mt-1 text-red-600">Error: {data.error}</p>
            )}
          </div>
        );

      case 'workflow_update':
        return (
          <div>
            <span className="font-semibold">{data.workflow_id}</span>
            <span className="mx-2">→</span>
            <span className="text-sm">{data.status}</span>
            {data.progress !== null && data.progress !== undefined && (
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${data.progress}%` }}
                ></div>
              </div>
            )}
          </div>
        );

      case 'system_alert':
        return (
          <div>
            <span className={`font-semibold ${
              data.severity === 'critical' || data.severity === 'error' ? 'text-red-700' :
              data.severity === 'warning' ? 'text-yellow-700' :
              'text-gray-700'
            }`}>
              {data.severity?.toUpperCase()}
            </span>
            <p className="text-sm mt-1">{data.message}</p>
            {data.component && (
              <p className="text-xs mt-1 text-gray-500">Component: {data.component}</p>
            )}
          </div>
        );

      default:
        return (
          <div>
            <pre className="text-xs overflow-x-auto">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        );
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-bold text-gray-800">
            Agent Activity Feed
          </h2>
          {connectionStatus()}
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {eventTypes.map(type => (
              <option key={type} value={type}>
                {type === 'all' ? 'All Events' : type.replace(/_/g, ' ').toUpperCase()}
              </option>
            ))}
          </select>

          <input
            type="text"
            placeholder="Filter by agent ID..."
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm flex-1 min-w-0 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          <button
            onClick={clearEvents}
            className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded-md text-sm font-medium transition-colors"
          >
            Clear
          </button>

          <label className="flex items-center text-sm">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="mr-2"
            />
            Auto-scroll
          </label>
        </div>
      </div>

      {/* Event Feed */}
      <div
        ref={feedRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-2"
      >
        {displayedEvents.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg mb-2">📡</p>
            <p>No events yet. Waiting for activity...</p>
          </div>
        ) : (
          displayedEvents.map((event, index) => {
            const colorClass = EVENT_COLORS[event.type] || EVENT_COLORS.default;
            const icon = EVENT_ICONS[event.type] || EVENT_ICONS.default;

            return (
              <div
                key={`${event.timestamp}-${index}`}
                className={`border-l-4 p-3 rounded ${colorClass} transition-all duration-200 hover:shadow-md`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-1">
                      <span className="text-lg mr-2">{icon}</span>
                      <span className="text-xs font-mono text-gray-600">
                        {formatTime(event.timestamp)}
                      </span>
                    </div>
                    {renderEventContent(event)}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Stats */}
      <div className="p-3 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>{displayedEvents.length} events shown</span>
          <span>{events.length} total events</span>
          {latency !== null && (
            <span className={`font-mono ${latency < 50 ? 'text-green-600' : 'text-yellow-600'}`}>
              Latency: {latency}ms {latency < 50 ? '✓' : '⚠'}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default AgentActivityFeed;
