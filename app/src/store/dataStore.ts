import { create } from "zustand";
import type { CalendarEvent, Task } from "../types/protocol";

interface DataState {
  tasks: Task[];
  events: CalendarEvent[];

  setTasks: (tasks: Task[]) => void;
  upsertTask: (task: Task) => void;
  removeTask: (id: string) => void;

  setEvents: (events: CalendarEvent[]) => void;
  upsertEvent: (event: CalendarEvent) => void;
  removeEvent: (id: string) => void;
}

const upsertById = <T extends { id: string }>(items: T[], item: T): T[] => {
  const idx = items.findIndex((i) => i.id === item.id);
  if (idx === -1) return [...items, item];
  const next = items.slice();
  next[idx] = item;
  return next;
};

export const useDataStore = create<DataState>()((set) => ({
  tasks: [],
  events: [],

  setTasks: (tasks) => set({ tasks }),
  upsertTask: (task) => set((s) => ({ tasks: upsertById(s.tasks, task) })),
  removeTask: (id) => set((s) => ({ tasks: s.tasks.filter((t) => t.id !== id) })),

  setEvents: (events) => set({ events }),
  upsertEvent: (event) => set((s) => ({ events: upsertById(s.events, event) })),
  removeEvent: (id) => set((s) => ({ events: s.events.filter((e) => e.id !== id) })),
}));
