/** Messages sent from client to server */
export interface ClientMessage {
  type: "message";
  text: string;
}

/** Events received from server */
export type ServerEvent = MessageEvent | StatusEvent | ErrorEvent;

export interface MessageEvent {
  type: "message";
  text: string;
  queued_at?: string;
}

export interface StatusEvent {
  type: "status";
  text: string;
}

export interface ErrorEvent {
  type: "error";
  text: string;
}

/** Chat message stored in the UI */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: number;
  queued_at?: string;
}

export type ConnectionStatus = "connected" | "connecting" | "disconnected";
