import { ChatWindow } from "./components/ChatWindow";
import { InputBar } from "./components/InputBar";
import { useWebSocket } from "./hooks/useWebSocket";
import { useChatStore } from "./store/chatStore";

export default function App() {
  const { sendMessage } = useWebSocket();
  const connectionStatus = useChatStore((s) => s.connectionStatus);
  const disconnected = connectionStatus !== "connected";

  return (
    <div className="dark flex flex-col h-screen overflow-hidden bg-background font-sans antialiased text-foreground">
      <div data-tauri-drag-region className="shrink-0 h-8" />
      {disconnected && (
        <div className="shrink-0 px-4 py-1.5 text-[12px] text-neutral-500 text-center border-b border-white/[.06]">
          {connectionStatus === "connecting" ? "Connecting..." : "Connection lost — reconnecting..."}
        </div>
      )}
      <ChatWindow />
      <InputBar onSend={sendMessage} />
    </div>
  );
}
