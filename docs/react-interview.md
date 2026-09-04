# 面试知识点：ReAct 循环 & Agent 架构

## 一、ReAct 是什么

### 1.1 概念

**ReAct = ReASONING + ACTing**

来自论文《ReAct: Synergizing Reasoning and Acting in Language Models》(Yao et al., 2022)

核心思想：让 LLM 在**推理（Thought）**和**行动（Action）**之间交替，每次行动后观察环境反馈（Observation），再继续推理，形成循环。

### 1.2 ReAct 循环图解

```
┌─────────────────────────────────────────────────────┐
│                    ReAct Loop                        │
│                                                     │
│   User Question                                     │
│        │                                            │
│        ▼                                            │
│   ┌─────────┐                                       │
│   │ Thought │  "用户想知道北京天气，我需要调用天气工具"  │
│   └────┬────┘                                       │
│        │                                            │
│        ▼                                            │
│   ┌─────────┐                                       │
│   │ Action  │  get_weather_by_city({"city": "北京"}) │
│   └────┬────┘                                       │
│        │                                            │
│        ▼                                            │
│   ┌─────────────┐                                   │
│   │ Observation │  "晴，15-25°C，湿度 40%"            │
│   └────┬────────┘                                   │
│        │                                            │
│        ▼                                            │
│   ┌─────────┐                                       │
│   │ Thought │  "已拿到数据，可以回答了"               │
│   └────┬────┘                                       │
│        │                                            │
│        ▼                                            │
│   ┌───────────────┐                                 │
│   │ Final Answer  │  "北京今天晴，15-25°C..."         │
│   └───────────────┘                                 │
│                                                     │
│   最多 N 轮（本项目 5 轮），超时 30 秒               │
└─────────────────────────────────────────────────────┘
```

### 1.3 代码实现（对应本项目）

```python
# backend/src/app/agent.py

for step in range(1, MAX_ROUNDS + 1):        # 最多 5 轮
    raw = chat(messages)                      # 调用 DeepSeek
    decision = parse_decision(raw)            # 解析 JSON

    if decision["type"] == "final":
        return decision["answer"], trace      # 直接返回

    if decision["type"] == "action":
        observation = _run_tool(...)          # 执行工具
        messages.append(...)                  # Observation 追加
        continue                             # 下一轮推理
```

---

## 二、Agent vs 普通 LLM API 调用

### 2.1 核心区别

| 维度 | 普通 LLM API | Agent |
|------|-------------|-------|
| 交互模式 | 一次请求 → 一次响应 | 多轮循环（推理→行动→观察） |
| 工具调用 | ❌ 不能 | ✅ 可以调用外部工具 |
| 信息来源 | 仅对话历史 | 对话历史 + 实时外部信息 |
| 自主性 | 被动回答 | 主动决策（决定用什么工具） |
| 循环 | 无 | ReAct 循环是核心 |
| 复杂度 | 简单 | 需要设计循环、工具、容错 |

### 2.2 一句话总结

> 普通 LLM API 调用是"大脑思考一次"，Agent 是"大脑思考→动手做→看结果→再思考"的循环。

### 2.3 什么时候用 Agent？

- 需要**实时信息**（天气、股票、数据库）
- 需要**执行动作**（发邮件、操作文件、调 API）
- 问题需要**多步推理**（先查 A → 再用 A 的结果查 B）
- 需要**自主决策**（不确定该用什么工具）

---

## 三、Agent 架构模式

### 3.1 ReAct（本项目使用）

```
Thought → Action → Observation → Thought → ... → Final Answer
```

- 优点：可解释性强（能看到每步推理）
- 缺点：每步都要调 LLM，延迟较高

### 3.2 Plan-and-Execute

```
Plan → Execute Step 1 → Execute Step 2 → ... → Replan → Final Answer
```

- 先制定计划，再逐步执行
- 适合复杂任务分解

### 3.3 Reflection

```
Action → Observation → Reflection → Improve → Action → ...
```

- 每步后反思，修正策略
- 适合需要自我纠错的场景

### 3.4 Multi-Agent

```
Agent A (研究员) → Agent B (程序员) → Agent C (测试员)
```

- 多个 Agent 协作，各自负责不同角色
- 适合复杂系统级任务

---

## 四、关键组件详解

### 4.1 System Prompt（定义输出格式）

```python
# 本项目的 system prompt 核心部分
"""
你必须严格按下面的 JSON 之一输出：
如果还需要调用工具，输出：
{"thought": "你的思考", "action": "工具名", "action_input": {"key": "value"}}

如果已经有把握回答用户，输出：
{"final_answer": "给用户的最终回答"}}
"""
```

**设计要点**:
- 明确 JSON 格式，减少模型输出不规范
- 只有 action 和 final_answer 两种输出，简化解析
- 工具列表由注册表动态生成，新增工具无需改 prompt

### 4.2 ToolRegistry（工具注册表）

```python
# 注册工具
registry.register(ToolSpec(
    name="get_weather_by_city",
    func=get_weather_by_city,
    description="查询指定城市的实时天气",
    parameters={"city": {"required": True, "type": "string"}},
))

# 调用工具（统一入口）
result = registry.call("get_weather_by_city", {"city": "北京"})
```

**设计要点**:
- `call()` 统一入口：查表 → 参数校验 → 执行 → 异常兜底
- 工具报错不崩溃，错误转为 Observation 回传模型
- `describe_all()` 动态生成工具描述，新增工具零配置

### 4.3 JSON 宽松解析

```python
def extract_json(text: str) -> dict:
    # 1. 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. 正则提取 {...} 块
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("没有找到 JSON")
    return json.loads(match.group(0))
```

**为什么需要**: LLM 输出不一定严格是 JSON，可能夹杂解释文字，需要宽松提取。

### 4.4 流式输出（WebSocket）

```
服务端推送事件序列:
  tool_call   →  前端渲染折叠卡片
  tool_result →  卡片显示结果
  token       →  逐字追加到助手气泡
  token       →
  done        →  流结束
```

**设计要点**:
- ReAct 决策用**非流式**（需要完整 JSON）
- 最终回答用**流式**（逐 token 打字效果）
- 工具事件和文本事件通过 `type` 字段区分

---

## 五、常见面试题 & 答案

### Q1: 什么是 ReAct？

**答**: ReAct = Reasoning + Acting，是让 LLM 在推理和行动之间交替的范式。模型先思考（Thought），决定调用什么工具（Action），获取工具结果（Observation），再继续推理，直到给出最终答案。

本项目中，我用 JSON 格式让模型输出决策：
```json
{"thought": "...", "action": "get_weather_by_city", "action_input": {"city": "北京"}}
```
模型看到 Observation 后继续推理，最多循环 5 轮。

---

### Q2: Agent 和普通 LLM API 调用的区别？

**答**: 核心区别是**循环**。

- 普通调用：一次请求→一次响应，模型只有对话历史
- Agent：多轮循环，模型可以调用工具、读取结果、修正回答

Agent 的本质是把 LLM 从"被动回答"升级为"主动决策+行动"。

---

### Q3: 你的 Agent 循环怎么实现的？

**答**: 核心在 `agent.py` 的 `run_agent()`:

1. 构造 messages（system prompt + 对话历史 + 用户问题）
2. 调用 DeepSeek 获取 JSON 决策
3. `parse_decision()` 解析：有 final_answer 直接返回，有 action 执行工具
4. 工具结果作为 Observation 追加到 messages
5. 重复 2-4，最多 5 轮
6. 超时 30 秒，解析失败重试 1 次

---

### Q4: 工具调用失败怎么办？

**答**: 三层容错：

1. **ToolRegistry**: 统一 try/except，异常转为文本 "工具执行失败: xxx"
2. **Observation 回传**: 错误信息作为 Observation 回传模型，模型可以决定重试或换工具
3. **轮数上限**: 最多 5 轮，不会死循环

---

### Q5: 为什么用 WebSocket 而不是 HTTP？

**答**: HTTP 是请求-响应模式，用户必须等完整回答。WebSocket 支持服务端主动推送，实现：
- 逐 token 流式输出（打字效果）
- 工具调用事件实时推送（tool_call → tool_result）
- 一次连接多次通信，减少握手开销

---

### Q6: ReAct 的优缺点？

**优点**:
- 可解释性强：能看到每步推理过程
- 灵活：模型自主决定用什么工具
- 容错：观察结果后可以修正策略

**缺点**:
- 延迟高：每步都要调 LLM
- 成本高：多次调用消耗 token
- 可能不稳定：模型输出格式不规范

---

### Q7: 怎么优化 Agent 的性能？

**答**:
1. **减少调用轮数**: 优化 system prompt，让模型更准确地选择工具
2. **并行工具调用**: 如果多个工具独立，可以并行执行
3. **缓存**: 对相同查询缓存工具结果
4. **异步**: 用 async/await 提升并发
5. **流式**: 最终回答用流式，减少用户感知延迟

---

### Q8: 工具注册表的设计思路？

**答**: 采用 ToolRegistry 模式：

- **ToolSpec**: 数据类，包含函数、描述、参数要求
- **registry.call()**: 统一入口，查表→校验→执行→异常兜底
- **describe_all()**: 动态生成工具描述，新增工具零配置

好处：工具报错不崩溃，新增工具无需改 prompt 和循环代码。

---

### Q9: 你的 System Prompt 怎么设计的？

**答**: 核心要求：
1. 定义输出格式：只输出 JSON，包含 thought/action/action_input 或 final_answer
2. 列出可用工具：由 ToolRegistry.describe_all() 动态生成
3. 约束 action 必须是工具列表中的名称
4. 约束 action_input 必须符合工具参数要求

---

### Q10: 如果模型输出不是合法 JSON 怎么办？

**答**: 三层处理：
1. **宽松解析**: 先尝试直接解析，失败则用正则提取 `{...}` 块
2. **重试一次**: 解析失败后提示模型"请严格只输出 JSON"，重试 1 次
3. **兜底回答**: 两次都失败，返回"抱歉，我暂时无法理解你的问题"

---

## 六、延伸知识点

### 6.1 Function Calling vs ReAct

| | Function Calling (OpenAI) | ReAct |
|---|---|---|
| 工具定义 | 预定义在 API 参数中 | 在 System Prompt 中定义 |
| 输出格式 | 结构化 JSON | 需要自己定义格式 |
| 循环 | 需要自己实现 | 需要自己实现 |
| 灵活性 | 较低 | 较高 |

本项目用 ReAct 是因为 DeepSeek 不支持原生 Function Calling，ReAct 更灵活。

### 6.2 Agent 框架对比

| 框架 | 特点 |
|------|------|
| LangChain | 最流行，生态丰富，但抽象层多 |
| LlamaIndex | 专注 RAG，向量检索强 |
| AutoGen | 微软出品，多 Agent 协作 |
| CrewAI | 多角色协作，简单易用 |
| 本项目 | 从零实现，理解底层原理 |

### 6.3 未来方向

- **Multi-Agent**: 多个 Agent 协作，如研究员+程序员+测试员
- **Planning**: 先制定计划再执行，如 TaskWeaver
- **Memory**: 长期记忆存储，如 MemGPT
- **Self-Reflection**: 自我反思和纠错
