export interface TraceStep {
  step: number;
  thought: string;
  tool: string;
  input: unknown;
  result: string;
}

export interface ChatResponse {
  reply: string;
  trace: TraceStep[];
}

export interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  trace?: TraceStep[];
  loading?: boolean;
}

export type WsEventType = "token" | "tool_call" | "tool_result" | "done" | "error";

export interface WsEvent {
  type: WsEventType;
  content?: string;
  step?: number;
  thought?: string;
  tool?: string;
  input?: Record<string, unknown>;
  result?: string;
  full_reply?: string;
  message?: string;
}

export type ConnectionStatus = "connected" | "disconnected" | "reconnecting";
