import type { ChatResponse } from "../types";

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
