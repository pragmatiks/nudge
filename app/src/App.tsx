import { Tabs, TabsContent } from "@/components/ui/tabs";
import { CalendarPanel } from "./components/CalendarPanel";
import { ChatWindow } from "./components/ChatWindow";
import { InputBar } from "./components/InputBar";
import { TabBar } from "./components/TabBar";
import { TasksPanel } from "./components/TasksPanel";
import { useWebSocket } from "./hooks/useWebSocket";
import { useChatStore } from "./store/chatStore";
import { useUIStore, type Tab } from "./store/uiStore";

export default function App() {
  const { sendMessage, sendAction, sendDataOp } = useWebSocket();
  const connectionStatus = useChatStore((s) => s.connectionStatus);
  const tab = useUIStore((s) => s.tab);
  const setTab = useUIStore((s) => s.setTab);
  const disconnected = connectionStatus !== "connected";

  return (
    <div className="dark flex flex-col h-screen overflow-hidden bg-background font-sans antialiased text-foreground">
      <div data-tauri-drag-region className="shrink-0 h-8" />
      {disconnected && (
        <div className="shrink-0 px-4 py-1.5 text-[12px] text-neutral-500 text-center border-b border-white/[.06]">
          {connectionStatus === "connecting" ? "Connecting..." : "Connection lost — reconnecting..."}
        </div>
      )}

      <Tabs
        value={tab}
        onValueChange={(v) => setTab(v as Tab)}
        className="flex-1 min-h-0 gap-0"
      >
        <TabsContent value="chat" className="flex-1 min-h-0 flex flex-col mt-0">
          <ChatWindow onAction={sendAction} />
          <InputBar onSend={sendMessage} />
        </TabsContent>
        <TabsContent value="tasks" className="flex-1 min-h-0 mt-0">
          <TasksPanel sendDataOp={sendDataOp} />
        </TabsContent>
        <TabsContent value="calendar" className="flex-1 min-h-0 mt-0">
          <CalendarPanel />
        </TabsContent>

        <TabBar />
      </Tabs>
    </div>
  );
}
