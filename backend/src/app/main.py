"""Day1 命令行入口：输入问题，运行 ReAct Agent，打印回答与工具调用轨迹。"""

import sys

from .agent import run_agent


def main() -> None:
    args = sys.argv[1:]
    question = " ".join(args) if args else input("请输入你的问题：").strip()
    if not question:
        print("问题不能为空")
        sys.exit(1)

    print("思考中...")
    reply, trace = run_agent(question)

    if trace:
        print("\n===== 工具调用轨迹 =====")
        for t in trace:
            print(f"[第{t['step']}步] 工具: {t['tool']}")
            print(f"  思考: {t['thought']}")
            print(f"  输入: {t['input']}")
            print(f"  结果: {t['result']}")
        print("========================")

    print(f"\n助手: {reply}")


if __name__ == "__main__":
    main()
