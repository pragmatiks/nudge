import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import { ComponentRenderer } from "./rich/ComponentRenderer";
import type { ChatMessage } from "../types/protocol";

interface Props {
  message: ChatMessage;
  onAction: (action: string, payload: Record<string, unknown>) => void;
}

export function MessageBubble({ message, onAction }: Props) {
  const isUser = message.role === "user";
  const time = new Date(message.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  // Rich component message
  if (message.component && message.componentProps) {
    return (
      <div className="flex px-4 py-1.5 justify-start">
        <div className="max-w-[85%]">
          <ComponentRenderer
            component={message.component}
            props={message.componentProps}
            onAction={onAction}
          />
          <div className="text-[11px] text-neutral-500 mt-1 text-right">
            {message.queued_at && "buffered · "}
            {time}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex px-4 py-1.5", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] px-3.5 py-2 text-[14px] leading-relaxed break-words rounded-lg",
          isUser
            ? "bg-bubble-user text-neutral-200 border border-white/[.08]"
            : "text-neutral-300",
        )}
      >
        {isUser ? (
          <span>{message.text}</span>
        ) : (
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="my-1">{children}</p>,
              ul: ({ children }) => <ul className="my-1 pl-5 list-disc">{children}</ul>,
              ol: ({ children }) => <ol className="my-1 pl-5 list-decimal">{children}</ol>,
              code: ({ children }) => (
                <code className="px-1.5 py-0.5 rounded bg-white/[.06] text-[13px] font-mono">
                  {children}
                </code>
              ),
              strong: ({ children }) => (
                <strong className="font-medium text-neutral-100">{children}</strong>
              ),
            }}
          >
            {message.text}
          </ReactMarkdown>
        )}
        <div className="text-[11px] text-neutral-500 mt-1 text-right">
          {message.queued_at && "buffered · "}
          {time}
        </div>
      </div>
    </div>
  );
}
