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
