import { useState } from "react";
import type { TraceStep } from "../types";

interface Props {
  steps: TraceStep[];
}

export function ToolCallCard({ steps }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mb-3 ml-12">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-700 transition-colors cursor-pointer bg-gray-50 hover:bg-gray-100 rounded-lg px-3 py-1.5 border border-gray-200"
      >
        <span className="text-sm">🔧</span>
        <span>
          调用了 {steps.length} 个工具
        </span>
        <span
          className={`ml-1 text-[10px] transition-transform ${
            open ? "rotate-90" : ""
          }`}
        >
          ▶
        </span>
      </button>

      {open && (
        <div className="mt-2 space-y-2">
          {steps.map((step) => (
            <div
              key={step.step}
              className="bg-white border border-gray-200 rounded-lg p-3 text-xs space-y-1.5 shadow-sm"
            >
              <div className="flex items-center gap-2 font-medium text-gray-700">
                <span>Step {step.step}</span>
                <span className="text-gray-400">|</span>
                <span className="text-blue-600">{step.tool}</span>
              </div>

              {step.thought && (
                <div className="text-gray-500 italic">
                  💭 {step.thought}
                </div>
              )}

              <div>
                <span className="font-medium text-gray-600">输入: </span>
                <span className="text-gray-800">
                  {typeof step.input === "object"
                    ? JSON.stringify(step.input)
                    : String(step.input)}
                </span>
              </div>

              <div>
                <span className="font-medium text-gray-600">结果: </span>
                <span className="text-gray-800">{step.result}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
