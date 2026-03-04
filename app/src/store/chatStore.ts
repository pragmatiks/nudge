import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ChatMessage, ConnectionStatus } from "../types/protocol";

interface ChatState {
  messages: ChatMessage[];
  connectionStatus: ConnectionStatus;
  toolStatus: string | null;

  addMessage: (msg: ChatMessage) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  setToolStatus: (status: string | null) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [],
      connectionStatus: "disconnected",
      toolStatus: null,

      addMessage: (msg) =>
        set((state) => ({ messages: [...state.messages, msg] })),

      setConnectionStatus: (connectionStatus) => set({ connectionStatus }),

      setToolStatus: (toolStatus) => set({ toolStatus }),
    }),
    {
      name: "nudge-chat",
      partialize: (state) => ({ messages: state.messages }),
    },
  ),
);
