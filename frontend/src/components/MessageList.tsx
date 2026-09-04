import { useEffect, useRef } from "react";
import type { DisplayMessage } from "../types";
import { ChatMessage } from "./ChatMessage";
import { ToolCallCard } from "./ToolCallCard";

interface Props {
  messages: DisplayMessage[];
}

export function MessageList({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
        试着问我点什么吧，比如「北京今天天气怎么样？」
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {messages.map((msg) => (
        <div key={msg.id}>
          {msg.role === "assistant" && msg.trace && msg.trace.length > 0 && (
            <ToolCallCard steps={msg.trace} />
          )}
          <ChatMessage
            role={msg.role}
            content={msg.content}
            loading={msg.loading}
          />
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
