import { MessageCircle, ListTodo, Calendar } from "lucide-react";
import { TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Tab } from "../store/uiStore";

interface TabDef {
  id: Tab;
  label: string;
  icon: typeof MessageCircle;
}

const TABS: TabDef[] = [
  { id: "chat", label: "Chat", icon: MessageCircle },
  { id: "tasks", label: "Tasks", icon: ListTodo },
  { id: "calendar", label: "Calendar", icon: Calendar },
];

/** Bottom navigation. Must be rendered inside a parent `<Tabs>` controlling the panel state. */
export function TabBar() {
  return (
    <TabsList className="shrink-0 w-full h-14 rounded-none bg-background border-t border-white/[.06] p-0 gap-0">
      {TABS.map(({ id, label, icon: Icon }) => (
        <TabsTrigger
          key={id}
          value={id}
          className="h-full flex-col gap-1 rounded-none border-0 text-[11px] data-[state=active]:bg-transparent data-[state=active]:shadow-none dark:data-[state=active]:bg-transparent dark:data-[state=active]:border-transparent"
        >
          <Icon className="size-5" />
          {label}
        </TabsTrigger>
      ))}
    </TabsList>
  );
}
