import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "../types/protocol";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const time = new Date(message.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className={cn("flex px-4 py-0.5", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] px-3 py-2 rounded-xl text-[15px] leading-relaxed break-words",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-bubble-assistant text-neutral-900",
        )}
      >
        {isUser ? (
          <span>{message.text}</span>
        ) : (
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="my-1">{children}</p>,
              ul: ({ children }) => <ul className="my-1 pl-5">{children}</ul>,
              ol: ({ children }) => <ol className="my-1 pl-5">{children}</ol>,
              code: ({ children }) => (
                <code
                  className={cn(
                    "px-1 py-px rounded text-[13px]",
                    isUser ? "bg-white/20" : "bg-black/[.06]",
                  )}
                >
                  {children}
                </code>
              ),
            }}
          >
            {message.text}
          </ReactMarkdown>
        )}
        <div className="text-[11px] opacity-60 mt-1 text-right">
          {message.queued_at && "buffered \u00B7 "}
          {time}
        </div>
      </div>
    </div>
  );
}
