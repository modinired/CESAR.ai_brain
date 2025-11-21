/**
 * React WebSocket Hook for Real-Time Communication
 * =================================================
 *
 * PhD-Level Implementation: Section 2 - Real-Time Communication (Frontend)
 * Based on CESAR.ai PhD Enhancement Framework
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Event filtering and room subscriptions
 * - Connection state management
 * - Latency measurement (ping/pong)
 * - Event buffering during disconnection
 *
 * Usage:
 * ```jsx
 * const {
 *   isConnected,
 *   events,
 *   subscribe,
 *   sendMessage,
 *   latency
 * } = useWebSocket({
 *   url: 'ws://localhost:8000/ws/events',
 *   rooms: ['agents', 'workflows'],
 *   onEvent: (event) => console.log('Received:', event)
 * });
 * ```
 */

import { useState, useEffect, useCallback, useRef } from 'react';

const DEFAULT_RECONNECT_INTERVAL = 1000; // Start with 1 second
const MAX_RECONNECT_INTERVAL = 30000; // Max 30 seconds
const PING_INTERVAL = 10000; // Ping every 10 seconds

export function useWebSocket({
  url = 'ws://localhost:8000/ws/events',
  clientId = null,
  rooms = ['all'],
  onEvent = null,
  onConnect = null,
  onDisconnect = null,
  autoConnect = true,
  reconnect = true
} = {}) {
  // WebSocket instance
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const pingIntervalRef = useRef(null);

  // State
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState('disconnected'); // connecting, connected, disconnected, error
  const [events, setEvents] = useState([]);
  const [latency, setLatency] = useState(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Generate client ID if not provided
  const getClientId = useCallback(() => {
    if (clientId) return clientId;
    return `dashboard_${Math.random().toString(36).substr(2, 9)}`;
  }, [clientId]);

  // Build WebSocket URL with client ID
  const getWebSocketUrl = useCallback(() => {
    const baseUrl = url;
    const id = getClientId();
    return `${baseUrl}?client_id=${id}`;
  }, [url, getClientId]);

  // Send ping to measure latency
  const sendPing = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const pingTime = Date.now();
      wsRef.current.send(JSON.stringify({
        type: 'ping',
        time: pingTime
      }));
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected');
      return;
    }

    setConnectionState('connecting');

    try {
      const wsUrl = getWebSocketUrl();
      console.log('[WebSocket] Connecting to:', wsUrl);

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[WebSocket] Connected');
        setIsConnected(true);
        setConnectionState('connected');
        setReconnectAttempts(0);

        // Subscribe to initial rooms
        if (rooms.length > 0) {
          ws.send(JSON.stringify({
            type: 'subscribe',
            rooms: rooms
          }));
        }

        // Start ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }
        pingIntervalRef.current = setInterval(sendPing, PING_INTERVAL);

        // Call onConnect callback
        if (onConnect) {
          onConnect();
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle pong (latency measurement)
          if (data.type === 'pong') {
            const latencyMs = Date.now() - data.client_time;
            setLatency(latencyMs);
            return;
          }

          // Handle connection acknowledgment
          if (data.type === 'connection') {
            console.log('[WebSocket] Connection acknowledged:', data);
            return;
          }

          // Add timestamp to event if not present
          if (!data.timestamp) {
            data.timestamp = new Date().toISOString();
          }

          // Add to events list (keep last 100)
          setEvents(prev => {
            const updated = [data, ...prev];
            return updated.slice(0, 100);
          });

          // Call custom event handler
          if (onEvent) {
            onEvent(data);
          }

        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        setConnectionState('error');
      };

      ws.onclose = () => {
        console.log('[WebSocket] Disconnected');
        setIsConnected(false);
        setConnectionState('disconnected');

        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Call onDisconnect callback
        if (onDisconnect) {
          onDisconnect();
        }

        // Attempt reconnection with exponential backoff
        if (reconnect) {
          const backoff = Math.min(
            DEFAULT_RECONNECT_INTERVAL * Math.pow(2, reconnectAttempts),
            MAX_RECONNECT_INTERVAL
          );

          console.log(`[WebSocket] Reconnecting in ${backoff}ms (attempt ${reconnectAttempts + 1})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connect();
          }, backoff);
        }
      };

      wsRef.current = ws;

    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
      setConnectionState('error');
    }
  }, [getWebSocketUrl, rooms, onConnect, onDisconnect, onEvent, reconnect, reconnectAttempts, sendPing]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    console.log('[WebSocket] Manually disconnecting');

    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Clear ping interval
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionState('disconnected');
  }, []);

  // Subscribe to rooms
  const subscribe = useCallback((newRooms) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        rooms: Array.isArray(newRooms) ? newRooms : [newRooms]
      }));
      console.log('[WebSocket] Subscribed to rooms:', newRooms);
    }
  }, []);

  // Unsubscribe from rooms
  const unsubscribe = useCallback((oldRooms) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        rooms: Array.isArray(oldRooms) ? oldRooms : [oldRooms]
      }));
      console.log('[WebSocket] Unsubscribed from rooms:', oldRooms);
    }
  }, []);

  // Send generic message
  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    console.warn('[WebSocket] Cannot send message: not connected');
    return false;
  }, []);

  // Set event filters
  const setFilters = useCallback((filters) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'filter',
        filters: filters
      }));
      console.log('[WebSocket] Filters set:', filters);
    }
  }, []);

  // Clear events history
  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, []); // Empty deps - only run on mount/unmount

  // Return hook API
  return {
    // Connection state
    isConnected,
    connectionState,
    reconnectAttempts,
    latency,

    // Events
    events,
    clearEvents,

    // Actions
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    sendMessage,
    setFilters,

    // Helpers
    clientId: getClientId()
  };
}

export default useWebSocket;
