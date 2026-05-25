# Tuning 模块

用于**自我迭代测试**和**交互体验优化**的独立工具集。

## 目录结构

```
tuning/
├── runner.py                    # 主入口：交互式 / 批量测试所有占卜类型
├── backend/
│   ├── test_prompts.py          # 直接调用 DivinationFactory，测试 prompt 构建
│   ├── test_api.py              # 调用实际 API 端点，测试 SSE 流式输出质量
│   ├── prompt_evaluator.py       # 本地轻量输出质量评估
│   └── prompts/
│       └── templates.py          # 从 Prompt Registry 导出的模板快照
├── frontend/
│   └── test_interactions.ts      # 前端 SSE 交互流程测试工具（浏览器 DevTools 可用）
├── scripts/
│   └── run_all.sh               # 一键运行所有测试的 shell 脚本
└── outputs/                     # 测试结果自动保存目录
```

## 快速开始

**前提：后端服务运行在 localhost:8000**

```bash
# 启动后端
python main.py

# 方式一：交互式选择测试类型
python tuning/runner.py

# 方式二：快速运行全部测试
bash tuning/scripts/run_all.sh

# 方式三：单独测试
python tuning/backend/test_prompts.py --type dream --verbose   # 查看 prompt 模板
python tuning/backend/test_api.py --type tarot --stream        # 查看 SSE 流输出
python tuning/backend/test_api.py --type all --save            # 扫描全部类型并保存结果
python tuning/backend/prompt_evaluator.py --type tarot --user-prompt "事业如何" --output "塔罗解析..."
```

## 核心工具说明

### 1. runner.py

直接调用 `DivinationFactory` 构建 prompt，无需启动服务即可预览效果。

```bash
python tuning/runner.py                      # 交互菜单
python tuning/runner.py --type tarot         # 指定类型
python tuning/runner.py --type all --save    # 全部 + 保存
```

### 2. test_prompts.py

查看各占卜类型的 **System Prompt + User Prompt** 组合，快速迭代 prompt 模板。

```bash
python tuning/backend/test_prompts.py                          # 全部类型
python tuning/backend/test_prompts.py --type tarot --verbose   # tarot 类型详细输出
```

### 3. prompt_evaluator.py

对模型输出做本地轻量评估，不依赖额外模型调用。当前评分维度：

| 维度 | 说明 |
|------|------|
| completeness | 输出长度、句子结尾、格式闭合 |
| relevance | 是否包含该占卜类型关键词，是否回应用户输入 |
| role_consistency | 是否出现角色逃逸或拒答表达 |
| format_quality | 是否有分段、列表或清晰结构 |
| fluency | 空格、占位值、逗号密度等基础可读性 |

```bash
python tuning/backend/prompt_evaluator.py \
  --type tarot \
  --user-prompt "事业如何" \
  --output "塔罗解析：过去..."
```

### 4. test_api.py

对 `/api/divination` 发真实 SSE 请求，测量延迟、chunk 数量、输出质量。

```bash
python tuning/backend/test_api.py --type dream --prompt "梦见蛇"  # 单类型
python tuning/backend/test_api.py --type all --save            # 扫描全部
python tuning/backend/test_api.py --type tarot --stream         # 显示原始 SSE 流
```

### 5. test_interactions.ts

前端交互流程验证工具。可在 Node.js 环境运行（需 fetch），或复制到浏览器 DevTools。

```typescript
import { runInteractionTest, runAllTests, ping } from './tuning/frontend/test_interactions';

// 验证连通性
await ping(); // true/false

// 测试单类型
await runInteractionTest('dream');

// 测试全部
await runAllTests();
```

## 测试流程建议

```
1. 修改 prompt 模板（src/divination/*.py）
        ↓
2. 运行 test_prompts.py 查看新 prompt 组合
        ↓
3. 运行 test_api.py --stream 观察实际输出
        ↓
4. 满意后，用 runner.py --save 保存本次测试结果到 outputs/
        ↓
5. 在前端 localhost:5173 页面做最终体验验证
```

## Prompt Registry

System Prompt、模型参数和评估样例集中定义在：

```
src/divination/prompt_registry.py
```

业务代码通过 `get_system_prompt()` 和 `DivinationFactory.get_params()` 读取当前 active variant。新增或调整 prompt 时，优先新增 variant 并切换 `active_variant`，再用 `test_prompts.py` 和 `prompt_evaluator.py` 验证。

当前 registry 快照见 `tuning/backend/prompts/templates.py`。

## Provider Profiles

`src/divination/prompt_registry.py` 还包含轻量 provider profiles：

| Provider | 用途 |
|----------|------|
| openai | 默认 OpenAI Chat Completions 兼容配置 |
| minimax | MiniMax OpenAI-compatible 接入说明 |
| custom | 前端自定义 API Base URL / Key / Model |

当前版本只记录 profile 元数据，不改变现有请求链路。
