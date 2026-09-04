import { useCallback, useEffect, useRef, useState } from "react";
import type { ConnectionStatus, DisplayMessage, TraceStep, WsEvent } from "../types";
import { createChatSocket } from "../api/client";

let idCounter = 0;
function nextId(): string {
  return `msg-${++idCounter}`;
}

function processEvent(
  event: WsEvent,
  activeMsgId: string | null,
  setMessages: React.Dispatch<React.SetStateAction<DisplayMessage[]>>,
  setLoading: React.Dispatch<React.SetStateAction<boolean>>
) {
  if (!activeMsgId) return;

  switch (event.type) {
    case "token":
      setMessages((prev) =>
        prev.map((m) =>
          m.id === activeMsgId
            ? { ...m, content: m.content + (event.content ?? ""), loading: false }
            : m
        )
      );
      break;

    case "tool_call":
      setMessages((prev) =>
        prev.map((m) => {
          if (m.id !== activeMsgId) return m;
          const newStep: TraceStep = {
            step: event.step ?? 0,
            thought: event.thought ?? "",
            tool: event.tool ?? "",
            input: event.input ?? {},
            result: "",
          };
          return { ...m, trace: [...(m.trace ?? []), newStep], loading: false };
        })
      );
      break;

    case "tool_result":
      setMessages((prev) =>
        prev.map((m) => {
          if (m.id !== activeMsgId) return m;
          const trace = (m.trace ?? []).map((s) =>
            s.step === event.step ? { ...s, result: event.result ?? "" } : s
          );
          return { ...m, trace };
        })
      );
      break;

    case "done":
      setMessages((prev) =>
        prev.map((m) =>
          m.id === activeMsgId ? { ...m, loading: false } : m
        )
      );
      setLoading(false);
      break;

    case "error":
      setMessages((prev) =>
        prev.map((m) =>
          m.id === activeMsgId
            ? {
                ...m,
                content: event.message ?? "未知错误",
                loading: false,
              }
            : m
        )
      );
      setLoading(false);
      break;
  }
}

export function useChat() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("disconnected");
  const historyRef = useRef<{ role: string; content: string }[]>([]);
  const activeMsgIdRef = useRef<string | null>(null);
  const socketRef = useRef<ReturnType<typeof createChatSocket> | null>(null);

  useEffect(() => {
    const socket = createChatSocket({
      onEvent: (event: WsEvent) => {
        processEvent(event, activeMsgIdRef.current, setMessages, setLoading);
      },
      onStatusChange: (status: ConnectionStatus) => setConnectionStatus(status),
    });
    socketRef.current = socket;

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, []);

  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || loading) return;

      const userMsg: DisplayMessage = {
        id: nextId(),
        role: "user",
        content: trimmed,
      };

      const assistantMsg: DisplayMessage = {
        id: nextId(),
        role: "assistant",
        content: "",
        loading: true,
      };

      activeMsgIdRef.current = assistantMsg.id;

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setLoading(true);

      historyRef.current.push(
        { role: "user", content: trimmed },
        { role: "assistant", content: "" }
      );

      socketRef.current?.send(trimmed, historyRef.current.slice(0, -2));
    },
    [loading]
  );

  return { messages, loading, connectionStatus, send };
}
