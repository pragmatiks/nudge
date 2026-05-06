import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Tab = "chat" | "tasks" | "calendar";

interface UIState {
  tab: Tab;
  setTab: (tab: Tab) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      tab: "chat",
      setTab: (tab) => set({ tab }),
    }),
    { name: "nudge-ui" },
  ),
);
