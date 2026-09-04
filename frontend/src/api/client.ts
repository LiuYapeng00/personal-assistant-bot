import type { ChatResponse, ConnectionStatus, WsEvent } from "../types";

const MAX_RECONNECT_ATTEMPTS = 5;
const BASE_RECONNECT_DELAY = 1000;

export async function sendMessage(
  message: string,
  history: { role: string; content: string }[] = []
): Promise<ChatResponse> {
  const res = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });

  if (!res.ok) {
    throw new Error(`请求失败: ${res.status}`);
  }

  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch("/health");
    const data = await res.json();
    return data.status === "ok";
  } catch {
    return false;
  }
}

export interface ChatSocketOptions {
  onEvent: (event: WsEvent) => void;
  onStatusChange: (status: ConnectionStatus) => void;
}

export function createChatSocket(options: ChatSocketOptions): {
  send: (message: string, history?: { role: string; content: string }[]) => void;
  close: () => void;
  reconnect: () => void;
} {
  let ws: WebSocket | null = null;
  let reconnectAttempts = 0;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let intentionalClose = false;

  function getWsUrl(): string {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/ws/chat`;
  }

  function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    ws = new WebSocket(getWsUrl());

    ws.onopen = () => {
      reconnectAttempts = 0;
      options.onStatusChange("connected");
    };

    ws.onmessage = (event) => {
      try {
        const data: WsEvent = JSON.parse(event.data);
        options.onEvent(data);
      } catch {
        console.error("Failed to parse WebSocket message:", event.data);
      }
    };

    ws.onclose = () => {
      if (intentionalClose) {
        options.onStatusChange("disconnected");
        return;
      }
      scheduleReconnect();
    };

    ws.onerror = () => {
      ws?.close();
    };
  }

  function scheduleReconnect() {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      options.onStatusChange("disconnected");
      return;
    }

    options.onStatusChange("reconnecting");
    const delay = BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts);
    reconnectAttempts++;

    reconnectTimer = setTimeout(() => {
      connect();
    }, delay);
  }

  function send(message: string, history: { role: string; content: string }[] = []) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ message, history }));
    }
  }

  function close() {
    intentionalClose = true;
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    ws?.close();
    ws = null;
  }

  function reconnect() {
    intentionalClose = false;
    reconnectAttempts = 0;
    close();
    intentionalClose = false;
    connect();
  }

  connect();

  return { send, close, reconnect };
}
