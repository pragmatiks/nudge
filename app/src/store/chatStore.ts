import { create } from "zustand";
import type { ChatMessage, ConnectionStatus } from "../types/protocol";

interface ChatState {
  messages: ChatMessage[];
  connectionStatus: ConnectionStatus;
  toolStatus: string | null;

  addMessage: (msg: ChatMessage) => void;
  setMessages: (msgs: ChatMessage[]) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  setToolStatus: (status: string | null) => void;
}

// Chat is single-sourced from the backend's history.json (24h rolling buffer).
// On WS connect we receive a `history_snapshot` and replace local state — so
// no localStorage persistence here, otherwise the two would drift apart.
export const useChatStore = create<ChatState>()((set) => ({
  messages: [],
  connectionStatus: "disconnected",
  toolStatus: null,

  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setMessages: (messages) => set({ messages }),
  setConnectionStatus: (connectionStatus) => set({ connectionStatus }),
  setToolStatus: (toolStatus) => set({ toolStatus }),
}));
