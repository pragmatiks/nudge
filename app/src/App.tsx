import { ChatWindow } from "./components/ChatWindow";
import { InputBar } from "./components/InputBar";
import { StatusBar } from "./components/StatusBar";
import { useWebSocket } from "./hooks/useWebSocket";

export default function App() {
  const { sendMessage } = useWebSocket();

  return (
    <div className="flex flex-col h-screen bg-white font-sans antialiased">
      <StatusBar />
      <ChatWindow />
      <InputBar onSend={sendMessage} />
    </div>
  );
}
