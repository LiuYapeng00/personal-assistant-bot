# Week 1 复盘：项目 1 - 个人助理 Bot

## 项目概览

从零搭建一个基于 ReAct 循环的智能个人助理，前后端分离，支持流式输出 + 工具调用可视化。

## 每日进度回顾

| 天 | 完成内容 | 产出 |
|----|---------|------|
| Day 1 | ReAct 核心循环，JSON 输出，工具执行，5 轮上限 | 命令行跑通"查天气→回答" |
| Day 2 | ToolRegistry 注册表，calculator + search_notes，异常回传 | 3 个工具可用，报错不崩溃 |
| Day 3 | FastAPI 路由、Pydantic、CORS、/health | POST /chat 接口跑通 |
| Day 4 | React 聊天界面 + 工具折叠卡片 | 浏览器可聊天，看到工具调用过程 |
| Day 5 | WebSocket 流式 + 断线重连 | 前端逐字渲染，断线自动恢复 |
| Day 6 | 端到端测试、README、复盘、面试题 | 35 个测试全部通过，文档完整 |

## 技术收获

### 1. ReAct 循环（核心）

**概念**: Reasoning + Acting，模型在推理和行动之间交替。

**实现要点**:
- System Prompt 定义输出格式：JSON 包含 thought/action/action_input 或 final_answer
- 宽松 JSON 解析：正则提取 `{...}` 块，兼容模型夹杂文字
- 轮数上限 5 轮 + 超时 30 秒，防止死循环
- 工具 Observation 追加到 messages，让模型看到结果继续推理

**踩坑**:
- DeepSeek 有时输出不是纯 JSON，需要宽松解析
- 流式模式下 ReAct 决策仍需同步收集完整 JSON，不能逐 token

### 2. ToolRegistry 工具注册表

**设计**:
- ToolSpec 数据类：函数 + 描述 + 参数要求
- `registry.call(name, kwargs)` 统一入口：查表→校验→执行→异常兜底
- `registry.describe_all()` 动态生成工具列表，新增工具无需改 prompt

**价值**: 工具报错不崩溃，错误转为 Observation 回传模型继续推理。

### 3. WebSocket 流式通信

**事件类型**: tool_call → tool_result → token... → done

**前端状态机**:
- 收到 tool_call/tool_result：渲染折叠卡片
- 收到 token：追加到当前助手消息
- 收到 done：结束流式，允许发送下一条
- 断线自动重连（指数退避）

### 4. uv 环境管理

```bash
uv init --python 3.12    # 初始化项目
uv add fastapi           # 添加依赖
uv run pytest            # 运行测试
uv sync                  # 同步环境
```

比 pip + venv 更快、更可靠。

## 遇到的问题 & 解决

| 问题 | 解决方案 |
|------|---------|
| DeepSeek 输出不规范 JSON | 正则提取 `{...}` + 重试 1 次 + 兜底回答 |
| 工具异常导致循环崩溃 | ToolRegistry 统一 try/except，错误转文本 |
| 前端消息顺序混乱 | 用 step 序号 + 事件类型保证渲染顺序 |
| CORS 跨域问题 | 固定端口 8000/5173，CORS 中间件配置 |
| 流式中工具决策需完整 JSON | ReAct 决策用非流式 chat()，最终回答用流式 |

## 代码质量

- **测试覆盖**: 35 个测试用例，覆盖 Agent 循环、工具注册表、API 接口、笔记搜索
- **Lint**: ruff (Python) + oxlint (TypeScript)，零警告
- **容错设计**: 工具异常、解析失败、轮数上限、超时，全覆盖

## 下周计划

- 项目 2：RAG 知识库问答
- 学习向量数据库 (ChromaDB) + Embedding + 检索增强生成
- 重点面试题：RAG 流程、向量相似度、chunking 策略

## 面试知识点总结

### ReAct 循环（高频）

**Q: 什么是 ReAct？和普通 LLM 调用有什么区别？**

A: ReAct = Reasoning + Acting。模型在 Thought（推理）和 Action（行动）之间交替，每次行动后观察环境反馈（Observation），再继续推理，直到给出 Final Answer。

和普通 LLM 调用的区别：
- 普通调用：一次请求→一次响应，模型只有对话历史
- Agent：多轮循环，模型能调用工具、读取结果、修正回答

**Q: 你的 Agent 循环是怎么实现的？**

A: 核心是 `agent.py` 的 `run_agent()` 函数：
1. 构造 messages（system + history + user）
2. 调用 DeepSeek 获取 JSON 决策
3. 解析：有 final_answer 返回，有 action 执行工具
4. 工具结果作为 Observation 追加到 messages
5. 重复 2-4，最多 5 轮

**Q: 工具调用失败怎么办？**

A: ToolRegistry 统一捕获异常，转为文本 "工具执行失败: xxx" 作为 Observation 回传模型，模型可以据此决定重试或换工具，循环不会崩溃。
