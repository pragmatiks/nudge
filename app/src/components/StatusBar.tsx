import { cn } from "@/lib/utils";
import { useChatStore } from "../store/chatStore";

const STATUS_DOT: Record<string, string> = {
  connected: "bg-status-connected",
  connecting: "bg-status-connecting",
  disconnected: "bg-status-disconnected",
};

export function StatusBar() {
  const connectionStatus = useChatStore((s) => s.connectionStatus);
  const toolStatus = useChatStore((s) => s.toolStatus);

  return (
    <div className="flex items-center gap-2 px-4 py-1.5 border-b bg-neutral-50 text-[13px] text-muted-foreground min-h-7">
      <div className={cn("size-2 rounded-full shrink-0", STATUS_DOT[connectionStatus])} />
      <span>
        {toolStatus ||
          (connectionStatus === "connected"
            ? "Nudge"
            : connectionStatus === "connecting"
              ? "Connecting..."
              : "Disconnected")}
      </span>
    </div>
  );
}
