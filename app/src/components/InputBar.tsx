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

  return (
    <div className="flex gap-2 px-3 py-2 border-t bg-neutral-50">
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? "Reconnecting..." : "Message..."}
        disabled={disabled}
        rows={1}
        className="flex-1 min-h-9 max-h-32 rounded-[20px] border-neutral-300 text-[15px] resize-none bg-white disabled:bg-neutral-100"
      />
      <Button
        size="icon"
        onClick={send}
        disabled={disabled || !text.trim()}
        className="rounded-full shrink-0"
      >
        <SendHorizontal className="size-4" />
      </Button>
    </div>
  );
}
