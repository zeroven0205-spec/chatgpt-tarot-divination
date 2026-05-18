# MiniMax M2.7 替代 OpenAI API 执行计划 ✅

> 计划日期：2026-04-29
> 项目：chatgpt-tarot-divination
> 基于评估：MINIMAX_MIGRATION_EVALUATION.md

---

## 阶段划分

```
阶段一：接口验证（独立于项目代码）
  └─ 1.1 确认 MiniMax API 协议兼容性
  └─ 1.2 流式响应格式验证
  └─ 1.3 参数支持范围验证

阶段二：配置层适配（不修改业务逻辑）
  └─ 2.1 后端配置项扩展
  └─ 2.2 前端 Settings 支持 MiniMax 配置

阶段三：代码适配（按需修改）
  └─ 3.1 流式解析层适配
  └─ 3.2 参数层适配
  └─ 3.3 Prompt 效果调优

阶段四：全链路测试
  └─ 4.1 7 种占卜类型全覆盖测试
  └─ 4.2 前端打字机效果验证
  └─ 4.3 速率限制验证

阶段五：上线部署
  └─ 5.1 环境配置
  └─ 5.2 回滚方案
```

---

## 阶段一：接口验证

> 目的：在修改项目代码之前，验证 MiniMax M2.7 API 的协议兼容性。
> 方式：独立脚本测试，不涉及项目代码。

### 1.1 确认 MiniMax API 端点格式

**需要确认的信息**：

| 信息项 | 验证方式 |
|--------|---------|
| API base URL | MiniMax 控制台获取 |
| 端点 path | 确认是否为 `/v1/chat/completions` 或 MiniMax 自定义路径 |
| API Key 获取方式 | Token Plan 控制台位置 |
| 认证方式 | Bearer Token 或其他 |

**验证步骤**：
```bash
# 发送一个最小化请求，确认端点可用
curl -X POST https://<MINIMAX_BASE_URL>/v1/chat/completions \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"model": "MiniMax-Embedding", "messages": [{"role":"user","content":"hi"}], "max_tokens": 10}'
```

**期望结果**：返回 200 或合理的 API 响应（不是 404/401/403）

### 1.2 流式响应格式验证

**验证脚本**：`test_minimax_stream.py`

```python
import httpx
import json

MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
API_KEY = "<YOUR_API_KEY>"
MODEL = "MiniMax-Text-01"

# 测试流式响应
with httpx.stream(
    "POST",
    f"{MINIMAX_BASE_URL}/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个占卜师"},
            {"role": "user", "content": "塔罗牌测试"}
        ],
        "max_tokens": 50,
        "temperature": 0.9,
        "stream": True
    },
    timeout=30.0
) as resp:
    print(f"Status: {resp.status_code}")
    for line in resp.iter_lines():
        if line.startswith("data:"):
            print(line)
```

**需要确认的格式兼容性**：

| 检查项 | OpenAI 格式 | MiniMax 需确认 |
|--------|------------|---------------|
| SSE 前缀 | `data:` | 是否相同 |
| JSON 结构 | `{"choices":[{"delta":{"content":"..."}}]}` | 是否相同 |
| 流结束标识 | `data: [DONE]` 或无更多数据 | 是否相同 |
| 编码格式 | UTF-8 | 是否相同 |

### 1.3 参数支持范围验证

**验证项**：

| 参数 | OpenAI 默认值 | 需要确认 MiniMax 是否支持 |
|------|-------------|----------------------|
| `max_tokens` | 1000 | 是否支持，是否有上限 |
| `temperature` | 0.9 | 是否支持，支持范围 |
| `top_p` | 1 | 是否支持 |
| `stream` | True | 是否支持 |

**验证方法**：分别用 `max_tokens=1000`、`temperature=0.9`、`top_p=1` 单独测试，观察是否报错或行为异常。

---

## 阶段二：配置层适配

> 原则：保留 OpenAI 配置的同时新增 MiniMax 配置，支持灵活切换。

### 2.1 后端配置项扩展

**文件**：`src/config.py`

新增字段：

```python
# MiniMax API settings
minimax_api_key: str = Field(default="", exclude=True)
minimax_api_base: str = "https://api.minimax.chat/v1"
minimax_model: str = "MiniMax-Text-01"

# Provider selection
llm_provider: str = "openai"  # "openai" | "minimax"
```

**影响**：仅增加配置项，不影响现有逻辑。

### 2.2 前端 Settings 页面支持

**需要前端展示的内容**（在现有自定义 API 配置基础上）：

| 字段 | 说明 |
|------|------|
| API Provider 选择 | OpenAI / MiniMax 下拉切换 |
| API Base URL | MiniMax 端点 |
| API Key | MiniMax Token |
| Model | MiniMax 模型名 |

**影响文件**：`frontend/src/pages/Settings.tsx`

---

## 阶段三：代码适配

> 根据阶段一验证结果，按需修改。如果 MiniMax 完全兼容 OpenAI 协议，此阶段可能跳过。

### 3.1 流式解析层适配（如需）

**文件**：`src/chatgpt_router.py:107-113`

**当前代码**：
```python
async for event in openai_stream:
    if event.choices and event.choices[0].delta and event.choices[0].delta.content:
        current_response = event.choices[0].delta.content
        yield f"data: {json.dumps(current_response)}\n\n"
```

**适配条件**：MiniMax 返回的 event 结构字段名与 OpenAI 不同

**适配方案**（如果字段不同）：
```python
# 方案A：如果 MiniMax 使用不同字段名
current_response = event.choices[0].delta.content  # 可能已是相同结构

# 方案B：如果需要从不同路径获取
current_response = event["choices"][0]["delta"]["content"]
```

### 3.2 参数层适配（如需）

**文件**：`src/chatgpt_router.py:84-88`

**当前硬编码**：
```python
openai_stream = await api_client.chat.completions.create(
    model=api_model,
    max_tokens=1000,
    temperature=0.9,
    top_p=1,
    stream=True,
    ...
)
```

**适配条件**：`top_p=1` 或 `max_tokens=1000` 在 MiniMax 上不支持

**适配方案**：
```python
# 从 settings 或请求头获取参数
params = {
    "model": api_model,
    "max_tokens": min(1000, settings.max_tokens_limit or 1000),
    "temperature": 0.9,
    "stream": True,
}
# 条件性添加 top_p（如果支持）
if settings.llm_provider == "openai":
    params["top_p"] = 1
```

### 3.3 Prompt 效果调优

**文件**：`src/divination/*.py`（7 个文件）

**调优条件**：MiniMax 对中文 system prompt 的指令遵循效果不佳

**可能的调优方向**：
- 简化 system prompt 措辞
- 将角色定义移至 user prompt 开头（few-shot 方式）
- 增加示例（example）强化角色扮演

---

## 阶段四：全链路测试

### 4.1 7 种占卜类型全覆盖测试

| prompt_type | 测试验证点 |
|-------------|----------|
| `tarot` | 塔罗牌解读是否流畅，抽卡逻辑是否正常 |
| `birthday` | 八字分析输出是否完整，中文日期格式是否正确 |
| `name` | 姓名五格评分是否合理 |
| `dream` | 梦境解读内容是否相关 |
| `new_name` | 起名建议是否结合了出生日期和五行 |
| `plum_flower` | 梅花易数数字占卜输出是否合理 |
| `fate` | 姻缘分析是否基于两个姓名 |

### 4.2 前端打字机效果验证

**验证点**：
- SSE 流是否持续接收到数据
- 打字机效果是否卡顿
- 流结束时光标是否正常处理

**测试方法**：在 `Settings` 页面切换不同 API 配置，分别测试塔罗牌占卜。

### 4.3 速率限制验证

**验证点**：
- 未认证用户速率限制是否仍生效（按 IP）
- 认证用户速率限制是否仍生效（按用户名）
- 自定义 API Key 时速率限制是否仍生效

---

## 阶段五：上线部署

### 5.1 环境配置

**`.env` 文件更新**：

```bash
# MiniMax 配置
minimax_api_key=xxx
minimax_api_base=https://api.minimax.chat/v1
minimax_model=MiniMax-Text-01

# 切换默认 provider
llm_provider=minimax

# 保留 OpenAI 作为备用
api_key=sk-xxx  # 可保留为空或填入占位
api_base=https://api.openai.com/v1
```

### 5.2 回滚方案

| 场景 | 回滚操作 |
|------|---------|
| MiniMax API 不稳定 | 将 `.env` 中 `llm_provider=openai` 切回 OpenAI |
| 流式解析失败 | 注释掉 `event.choices[0].delta.content` 适配代码，恢复原始逻辑 |
| Prompt 效果差 | `.env` 切回 OpenAI，保留代码但不加适配标记 |

**回滚判断标准**：
- 7 种占卜连续 3 次返回空响应或乱码 → 触发回滚
- 速率限制报 500 错误 → 检查适配代码

---

## 执行优先级

```
第一步（必须）  → 阶段一：接口验证（独立脚本，确认 MiniMax 协议兼容性）
第二步（必须）  → 阶段二：配置层扩展（src/config.py + 前端 Settings）
第三步（按需）  → 阶段三：如阶段一发现兼容差异，进行代码适配
第四步（必须）  → 阶段四：全链路测试（7 种占卜全覆盖）
第五步（必须）  → 阶段五：上线 + 回滚方案文档化
```

---

## 风险登记与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| MiniMax SSE 格式与 OpenAI 不兼容 | 中 | 高 | 阶段三适配流式解析代码 |
| `top_p` 参数 MiniMax 不支持 | 中 | 低 | 删除 `top_p` 参数 |
| `max_tokens=1000` 超限 | 低 | 低 | 降低到 512 |
| Prompt 效果差（角色扮演弱） | 中 | 中 | 调优 prompt 措辞 |
| MiniMax API Key 泄露 | 低 | 高 | 使用 `.env` exclude=True 保护 |
| 速率限制冲突 | 低 | 低 | 使用 provider 维度区分限流 key |
