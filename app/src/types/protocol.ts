/** Messages sent from client to server */
export type ClientMessage =
  | TextMessage
  | ToolResponseMessage
  | ActionMessage
  | DataOpMessage;

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

export type DataOpType =
  | "task_create"
  | "task_update"
  | "task_complete"
  | "task_delete"
  | "event_create"
  | "event_update"
  | "event_delete";

/** Client-driven CRUD on tasks and calendar events. */
export interface DataOpMessage {
  type: DataOpType;
  payload: Record<string, unknown>;
}

/** Events received from server */
export type ServerEvent =
  | MessageEvent
  | UserMessageEvent
  | StatusEvent
  | ErrorEvent
  | ToolRequestEvent
  | ComponentEvent
  | TasksSnapshotEvent
  | TaskAddedEvent
  | TaskUpdatedEvent
  | TaskDeletedEvent
  | EventsSnapshotEvent
  | EventAddedEvent
  | EventUpdatedEvent
  | EventDeletedEvent
  | HistorySnapshotEvent;

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

/** Native task — kept in sync with the server via WebSocket events. */
export interface Task {
  id: string;
  title: string;
  notes: string;
  due: string | null;
  /** 1=urgent, 2=high, 3=medium, 4=normal/none */
  priority: number;
  completed: boolean;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CalendarEvent {
  id: string;
  title: string;
  description: string;
  start: string;
  end: string;
  location: string;
  all_day: boolean;
  created_at: string;
  updated_at: string;
}

export interface TasksSnapshotEvent {
  type: "tasks_snapshot";
  tasks: Task[];
}

export interface TaskAddedEvent {
  type: "task_added";
  task: Task;
}

export interface TaskUpdatedEvent {
  type: "task_updated";
  task: Task;
}

export interface TaskDeletedEvent {
  type: "task_deleted";
  id: string;
}

export interface EventsSnapshotEvent {
  type: "events_snapshot";
  events: CalendarEvent[];
}

export interface EventAddedEvent {
  type: "event_added";
  event: CalendarEvent;
}

export interface EventUpdatedEvent {
  type: "event_updated";
  event: CalendarEvent;
}

export interface EventDeletedEvent {
  type: "event_deleted";
  id: string;
}

/** Snapshot of the backend's rolling 24-hour message history, sent on connect. */
export interface HistorySnapshotEvent {
  type: "history_snapshot";
  messages: { ts: string; direction: "user" | "assistant"; text: string }[];
}
