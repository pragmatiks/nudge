/** Messages sent from client to server */
export type ClientMessage = TextMessage | ToolResponseMessage | ActionMessage;

export interface TextMessage {
  type: "message";
  text: string;
}

export interface ToolResponseMessage {
  type: "tool_response";
  id: string;
  result?: Record<string, unknown>;
  error?: string;
}

export interface ActionMessage {
  type: "action";
  action: string;
  payload: Record<string, unknown>;
}

/** Events received from server */
export type ServerEvent =
  | MessageEvent
  | UserMessageEvent
  | StatusEvent
  | ErrorEvent
  | ToolRequestEvent
  | ComponentEvent;

export interface MessageEvent {
  type: "message";
  text: string;
  queued_at?: string;
}

export interface UserMessageEvent {
  type: "user_message";
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

export interface ToolRequestEvent {
  type: "tool_request";
  id: string;
  name: string;
  args: Record<string, unknown>;
}

export interface ComponentEvent {
  type: "component";
  component: string;
  props: Record<string, unknown>;
  queued_at?: string;
}

/** Chat message stored in the UI */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: number;
  queued_at?: string;
  /** Rich UI component data */
  component?: string;
  componentProps?: Record<string, unknown>;
}

export type ConnectionStatus = "connected" | "connecting" | "disconnected";
