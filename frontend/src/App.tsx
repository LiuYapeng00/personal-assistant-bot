import { useState } from "react";
import { useChat } from "./hooks/useChat";
import { MessageList } from "./components/MessageList";

function App() {
  const { messages, loading, connectionStatus, send } = useChat();
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim() || loading) return;
    send(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const statusLabel =
    connectionStatus === "connected"
      ? "已连接"
      : connectionStatus === "reconnecting"
        ? "重连中..."
        : "未连接";

  const statusColor =
    connectionStatus === "connected"
      ? "bg-green-400"
      : connectionStatus === "reconnecting"
        ? "bg-yellow-400"
        : "bg-red-400";

  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 px-4 py-3 flex items-center justify-between shrink-0">
        <h1 className="text-base font-semibold text-gray-800">
          个人助理 Bot
        </h1>
        <div className="flex items-center gap-1.5 text-xs text-gray-400">
          <span className={`w-2 h-2 rounded-full ${statusColor}`} />
          {statusLabel}
        </div>
      </div>

      {/* Messages */}
      <MessageList messages={messages} />

      {/* Input */}
      <div className="border-t border-gray-200 p-4 shrink-0">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 transition-colors"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-5 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors shrink-0"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
