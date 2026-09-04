import { useCallback, useRef, useState } from "react";
import type { ChatResponse, DisplayMessage } from "../types";
import { sendMessage } from "../api/client";

let idCounter = 0;
function nextId(): string {
  return `msg-${++idCounter}`;
}

export function useChat() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const historyRef = useRef<{ role: string; content: string }[]>([]);

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || loading) return;

      const userMsg: DisplayMessage = {
        id: nextId(),
        role: "user",
        content: trimmed,
      };

      const loadingMsg: DisplayMessage = {
        id: nextId(),
        role: "assistant",
        content: "",
        loading: true,
      };

      setMessages((prev) => [...prev, userMsg, loadingMsg]);
      setLoading(true);

      try {
        const data: ChatResponse = await sendMessage(
          trimmed,
          historyRef.current
        );

        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingMsg.id
              ? { ...m, content: data.reply, trace: data.trace, loading: false }
              : m
          )
        );

        historyRef.current.push(
          { role: "user", content: trimmed },
          { role: "assistant", content: data.reply }
        );
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "未知错误";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingMsg.id
              ? { ...m, content: `出错了: ${errorMsg}`, loading: false }
              : m
          )
        );
      } finally {
        setLoading(false);
      }
    },
    [loading]
  );

  return { messages, loading, send };
}
