import { useState, useCallback, type KeyboardEvent } from "react";
import { SendHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useChatStore } from "../store/chatStore";

interface Props {
  onSend: (text: string) => void;
}

export function InputBar({ onSend }: Props) {
  const [text, setText] = useState("");
  const connectionStatus = useChatStore((s) => s.connectionStatus);
  const disabled = connectionStatus !== "connected";

  const send = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;

    useChatStore.getState().addMessage({
      id: crypto.randomUUID(),
      role: "user",
      text: trimmed,
      timestamp: Date.now(),
    });

    onSend(trimmed);
    setText("");
  }, [text, disabled, onSend]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const toolStatus = useChatStore((s) => s.toolStatus);

  return (
    <div className="flex flex-col border-t border-white/[.06]">
      {toolStatus && (
        <div className="px-4 pt-1.5 text-[12px] text-neutral-500 truncate">{toolStatus}</div>
      )}
      <div className="flex gap-2 px-3 py-2">
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? "Reconnecting..." : "Message..."}
        disabled={disabled}
        rows={1}
        className="flex-1 min-h-9 max-h-32 rounded-lg border-white/[.08] text-[14px] resize-none bg-white/[.04] text-neutral-200 placeholder:text-neutral-500 focus-visible:ring-white/[.12] disabled:opacity-40"
      />
      <Button
        size="icon"
        variant="ghost"
        onClick={send}
        disabled={disabled || !text.trim()}
        className="rounded-lg shrink-0 text-neutral-400 hover:text-neutral-200 hover:bg-white/[.06] disabled:opacity-30"
      >
        <SendHorizontal className="size-4" />
      </Button>
      </div>
    </div>
  );
}
