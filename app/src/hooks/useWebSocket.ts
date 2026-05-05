import { useEffect, useRef, useCallback } from "react";
import { useChatStore } from "../store/chatStore";
import { executeClientTool } from "../lib/clientTools";
import type { ServerEvent } from "../types/protocol";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8787/ws";
const WS_TOKEN = import.meta.env.VITE_API_TOKEN || "";

const RECONNECT_BASE = 3000;
const RECONNECT_CAP = 30000;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const { addMessage, setConnectionStatus, setToolStatus } = useChatStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus("connecting");

    const ws = new WebSocket(`${WS_URL}?token=${WS_TOKEN}`);
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectAttempt.current = 0;
      setConnectionStatus("connected");
      setToolStatus(null);
    };

    ws.onmessage = (event) => {
      const data: ServerEvent = JSON.parse(event.data);

      switch (data.type) {
        case "message":
          setToolStatus(null);
          addMessage({
            id: crypto.randomUUID(),
            role: "assistant",
            text: data.text,
            timestamp: Date.now(),
            queued_at: data.queued_at,
          });
          break;
        case "user_message":
          addMessage({
            id: crypto.randomUUID(),
            role: "user",
            text: data.text,
            timestamp: Date.now(),
            queued_at: data.queued_at,
          });
          break;
        case "component":
          setToolStatus(null);
          console.log("[component]", data.component, JSON.stringify(data.props));
          addMessage({
            id: crypto.randomUUID(),
            role: "assistant",
            text: "",
            timestamp: Date.now(),
            queued_at: data.queued_at,
            component: data.component,
            componentProps: data.props,
          });
          break;
        case "tool_request":
          executeClientTool(data.name, data.args)
            .then((result) =>
              ws.send(JSON.stringify({ type: "tool_response", id: data.id, result })),
            )
            .catch((err) =>
              ws.send(
                JSON.stringify({ type: "tool_response", id: data.id, error: err.message }),
              ),
            );
          break;
        case "status":
          setToolStatus(data.text);
          break;
        case "error":
          setToolStatus(null);
          addMessage({
            id: crypto.randomUUID(),
            role: "assistant",
            text: `Error: ${data.text}`,
            timestamp: Date.now(),
          });
          break;
      }
    };

    ws.onclose = () => {
      setConnectionStatus("disconnected");
      setToolStatus(null);
      scheduleReconnect();
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [addMessage, setConnectionStatus, setToolStatus]);

  const scheduleReconnect = useCallback(() => {
    const delay = Math.min(
      RECONNECT_BASE * 2 ** reconnectAttempt.current,
      RECONNECT_CAP,
    );
    reconnectAttempt.current++;
    reconnectTimer.current = setTimeout(connect, delay);
  }, [connect]);

  const sendMessage = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "message", text }));
    }
  }, []);

  const sendAction = useCallback((action: string, payload: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "action", action, payload }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { sendMessage, sendAction };
}
