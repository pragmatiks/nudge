import { useEffect, useRef, useCallback } from "react";
import { useChatStore } from "../store/chatStore";
import { useDataStore } from "../store/dataStore";
import { executeClientTool } from "../lib/clientTools";
import type { ClientMessage, DataOpType, ServerEvent } from "../types/protocol";

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
      const evt: ServerEvent = JSON.parse(event.data);

      switch (evt.type) {
        case "message":
          setToolStatus(null);
          addMessage({
            id: crypto.randomUUID(),
            role: "assistant",
            text: evt.text,
            timestamp: Date.now(),
            queued_at: evt.queued_at,
          });
          break;
        case "user_message":
          addMessage({
            id: crypto.randomUUID(),
            role: "user",
            text: evt.text,
            timestamp: Date.now(),
            queued_at: evt.queued_at,
          });
          break;
        case "component":
          setToolStatus(null);
          addMessage({
            id: crypto.randomUUID(),
            role: "assistant",
            text: "",
            timestamp: Date.now(),
            queued_at: evt.queued_at,
            component: evt.component,
            componentProps: evt.props,
          });
          break;
        case "tool_request":
          executeClientTool(evt.name, evt.args)
            .then((result) =>
              ws.send(JSON.stringify({ type: "tool_response", id: evt.id, result })),
            )
            .catch((err) =>
              ws.send(
                JSON.stringify({ type: "tool_response", id: evt.id, error: err.message }),
              ),
            );
          break;
        case "status":
          setToolStatus(evt.text);
          break;
        case "error":
          setToolStatus(null);
          addMessage({
            id: crypto.randomUUID(),
            role: "assistant",
            text: `Error: ${evt.text}`,
            timestamp: Date.now(),
          });
          break;
        case "tasks_snapshot":
          useDataStore.getState().setTasks(evt.tasks);
          break;
        case "task_added":
        case "task_updated":
          useDataStore.getState().upsertTask(evt.task);
          break;
        case "task_deleted":
          useDataStore.getState().removeTask(evt.id);
          break;
        case "events_snapshot":
          useDataStore.getState().setEvents(evt.events);
          break;
        case "event_added":
        case "event_updated":
          useDataStore.getState().upsertEvent(evt.event);
          break;
        case "event_deleted":
          useDataStore.getState().removeEvent(evt.id);
          break;
        case "history_snapshot": {
          // The backend's history.json is the source of truth for chat
          // (24h rolling buffer). Always replace — the index-coupled compare
          // we used to do silently dropped reorders/edits at the same ts.
          useChatStore.getState().setMessages(
            evt.messages.map((m) => ({
              id: `${m.ts}-${m.direction}`,
              role: m.direction,
              text: m.text,
              timestamp: Date.parse(m.ts) || Date.now(),
            })),
          );
          break;
        }
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

  const send = useCallback((msg: ClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const sendMessage = useCallback(
    (text: string) => send({ type: "message", text }),
    [send],
  );

  const sendAction = useCallback(
    (action: string, payload: Record<string, unknown>) =>
      send({ type: "action", action, payload }),
    [send],
  );

  const sendDataOp = useCallback(
    (type: DataOpType, payload: Record<string, unknown>) => send({ type, payload }),
    [send],
  );

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { sendMessage, sendAction, sendDataOp };
}
