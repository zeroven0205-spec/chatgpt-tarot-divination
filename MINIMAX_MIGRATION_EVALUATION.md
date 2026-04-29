# MiniMax M2.7 Token Plan API 替代 OpenAI API 评估报告

> 评估日期：2026-04-29
> 项目：chatgpt-tarot-divination

---

## 一、项目中 OpenAI API 的使用方式

**调用点**：`src/chatgpt_router.py:84` — 仅此一处

```python
openai_stream = await api_client.chat.completions.create(
    model=api_model,        # 默认 gpt-3.5-turbo，可被 x-api-model 覆盖
    max_tokens=1000,        # 硬编码 1000
    temperature=0.9,        # 硬编码 0.9
    top_p=1,                # 硬编码 1
    stream=True,            # 流式输出
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
)
```

### 关键特征

| 维度 | 描述 |
|------|------|
| **API 类型** | Chat Completions（对话补全），非 Function Calling / Tools / Vision |
| **流式** | `stream=True`，后端透传 SSE 到前端，前端打字机效果 |
| **消息结构** | 固定 2 条消息：`system`（角色设定） + `user`（用户输入） |
| **认证方式** | API Key + 可选 Base URL，均通过 `AsyncOpenAI` 客户端注入 |
| **自定义覆盖** | 支持 `x-api-key` / `x-api-url` / `x-api-model` 三路请求头覆盖 |
| **调用频率** | 受速率限制保护（游客 60/小时，用户 600/小时） |

### 7 种占卜类型的 Prompt 模式

每种占卜类型通过 `DivinationFactory` 注册，提供 `system_prompt`（角色定义）和 `user_prompt`（用户问题）：

| prompt_type | system_prompt 角色 | user_prompt 来源 |
|-------------|-------------------|-----------------|
| `tarot` | 塔罗占卜师 | 用户输入的问题（≤40字） |
| `birthday` | 八字算命师 | 用户生日时间戳 |
| `name` | 姓名五格算命师 | 用户输入的姓名 |
| `dream` | 周公解梦师 | 用户描述的梦境（≤40字） |
| `new_name` | 起名师 | 姓氏 + 性别 + 生日 + 期望 |
| `plum_flower` | 梅花易数占卜师 | 两个数字 |
| `fate` | 姻缘助手 | 两个姓名 |

---

## 二、MiniMax M2.7 Token Plan API 兼容性分析

### 1. API 协议兼容性

| 维度 | OpenAI 风格 | MiniMax M2.7 | 兼容性评估 |
|------|------------|--------------|-----------|
| **endpoint** | `POST /v1/chat/completions` | 需确认 MiniMax 端点格式 | ⚠️ 需确认是否兼容 OpenAI endpoint path |
| **base_url** | `https://api.openai.com/v1` | MiniMax 有独立域名 | ⚠️ `api_base` 配置需修改为 MiniMax 地址 |
| **流式响应** | SSE via `stream=True` | 需确认是否支持 SSE 格式 | ⚠️ 需确认 MiniMax streaming 格式是否与 OpenAI 一致 |
| **模型参数** | `model`, `messages`, `temperature`, `max_tokens`, `top_p` | 需确认参数命名 | ⚠️ `max_tokens=1000` / `temperature=0.9` / `top_p=1` 可能需要调整 |

### 2. 消息格式兼容性

OpenAI 消息格式：
```json
{"role": "system", "content": "..."}
{"role": "user", "content": "..."}
```

MiniMax 大模型 API 如果采用 OpenAI 兼容格式，则 `messages` 数组无需修改；如果使用自定义格式，则 `src/chatgpt_router.py` 中 `messages` 构建部分需要调整。

### 3. 流式输出格式兼容性

当前 SSE 格式：
```
data: {"content":"今"}\n\n
data: {"content":"天的"}\n\n
```

前端 `@microsoft/fetch-event-source` 期望每个 SSE data 块为字符串（被 JSON.parse 解析）。如果 MiniMax 流式输出格式不同，前端渲染层可能需要调整。

---

## 三、需要修改的内容（评估层面）

| 层级 | 文件 | 修改内容 |
|------|------|---------|
| **配置层** | `src/config.py` | 新增 `minimax_api_key` / `minimax_base_url` / `minimax_model` 配置项，或复用车载 `api_key`/`api_base` |
| **客户端层** | `src/chatgpt_router.py:19,72-75` | `AsyncOpenAI` 客户端的 base_url 和 api_key 需要能切换为 MiniMax；当前支持 `x-api-url`/`x-api-key` 头覆盖已有机制，无需改代码即可接入 |
| **Prompt 层** | `src/divination/*.py`（7个文件） | system_prompt 中的角色定义是否需要调整取决于 MiniMax 模型的指令遵循能力 |
| **流式解析层** | `src/chatgpt_router.py:107-113` | `event.choices[0].delta.content` 解析逻辑如果 MiniMax 返回的 event 字段名不同则需要修改 |
| **前端层** | `frontend/src/hooks/useDivination.ts` | SSE data 解析逻辑可能需要调整 |
| **硬编码参数** | `chatgpt_router.py:86-88` | `max_tokens=1000`, `temperature=0.9`, `top_p=1` 需要确认 MiniMax 是否支持这些参数 |

---

## 四、关键发现：已有自定义 API 覆盖机制

项目中 **已经实现了** 自定义 API Key/URL/Model 的请求头覆盖机制：

```python
# src/chatgpt_router.py:67-75
custom_base_url = request.headers.get("x-api-url")
custom_api_key = request.headers.get("x-api-key")
custom_api_model = request.headers.get("x-api-model")
...
if custom_base_url and custom_api_key:
    api_client = AsyncOpenAI(api_key=custom_api_key, base_url=custom_base_url)
elif custom_api_key:
    api_client = AsyncOpenAI(api_key=custom_api_key, base_url=settings.api_base)
```

前端 Settings 页面也支持用户填入自定义 API 配置。这意味着：

> **如果 MiniMax M2.7 提供 OpenAI 兼容的 base_url + API key，用户只需在前端 Settings 页面填入 MiniMax 的 API Key 和 Base URL，无需修改任何后端代码即可切换。**

---

## 五、结论与风险

### 结论

| 结论 | 说明 |
|------|------|
| **可替代性** | 理论可行，核心是 Chat Completions + Streaming，MiniMax M2.7 如果提供 OpenAI 兼容 endpoint，改造成本低 |
| **最小改动力** | 如果 MiniMax M2.7 是 OpenAI 兼容 API，**最多只需修改 `.env` 配置**，已有请求头覆盖机制无需改代码 |
| **完全不改代码的条件** | MiniMax API 必须是：OpenAI-compatible endpoint + SSE streaming + `choices[0].delta.content` 格式 |

### 风险点

| 风险 | 说明 |
|------|------|
| 流式响应格式差异 | MiniMax 流式输出的 event 格式是否与 OpenAI 一致（`data: {...}` SSE 块） |
| event 字段名差异 | `choices[0].delta.content` 解析逻辑如果 MiniMax 使用不同字段名会导致流式输出失效 |
| `top_p` 参数支持 | 部分国产模型 API 不支持 `top_p` 参数 |
| `max_tokens` 限制 | 部分模型有输入 token 上限限制，`max_tokens=1000` 需确认是否在范围内 |
| Prompt 指令遵循 | 7 个占卜 system_prompt 中包含复杂角色定义（如"你是一个姻缘助手..."），MiniMax 对中文系统指令的遵循程度需实测 |

### 需要上线前实测确认

1. MiniMax M2.7 是否支持 `POST /v1/chat/completions` OpenAI 兼容端点
2. `stream=True` 时 SSE 格式是否为 `data: {"choices":[{"delta":{"content":"..."}}]}\n\n`
3. `max_tokens=1000`, `temperature=0.9`, `top_p=1` 是否全部支持
4. 中文 system prompt 的指令遵循效果是否满足 7 种占卜角色扮演的需求
