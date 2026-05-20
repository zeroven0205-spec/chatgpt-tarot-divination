# 自我迭代测试和交互体验优化工具集计划

> 规划日期：2026-05-18
> 更新日期：2026-05-18（第一轮修复完成）
> 项目：chatgpt-tarot-divination
> 目标：建立独立于业务的 Prompt Tuning 框架 + 交互体验诊断工具集

---

## 一、背景与目标

当前项目的 7 种占卜 Prompt（`src/divination/*.py`）存在以下问题：

- **硬编码无调优机制** — system prompt 是字符串常量，无法按类型配置参数（temperature/max_tokens）
- **无质量评估** — 流式输出无截断检测、无完整性验证、无用户满意度追踪
- **交互体验黑盒** — 前端 SSE 处理、错误状态、流结束判断缺乏系统性诊断手段
- **无法 A/B 测试** — 修改 prompt 需要改代码，无法灰度验证效果

本计划旨在构建**独立工具集**，在不修改业务代码的情况下，对上述问题进行系统性诊断和优化。

> ### 实施状态（2026-05-18 更新）
> - ✅ **Prompt 参数化** — 已实现为 `src/divination/base.py:DIVINATION_PARAMS`，7种类型差异化配置
> - ✅ **SSE 协议标准化** — 后端发送 `[DONE]` 标识，前端识别处理
> - ⏳ **Prompt 版本化 / A/B 测试框架** — 尚未实施（可选）
> - ⏳ **流式输出诊断工具** — 尚未实施（可选）
> - ⏳ **交互体验测试工具** — 尚未实施（可选）

---

## 二、工具集架构

```
tools/
├── prompt_tuning/              # Prompt 调优工具
│   ├── evaluator.py            # Prompt 效果评估器
│   ├── param_config.py         # 类型参数配置
│   ├── prompt_registry.py      # Prompt 版本注册表
│   └── ab_tester.py           # A/B 测试框架
├── streaming_diagnostics/       # 流式输出诊断
│   ├──完整性检测.py
│   ├── 延迟分析.py
│   └── sse_parser.py           # SSE 协议解析器
├── interaction_testing/        # 交互体验测试
│   ├── playwright_runner.py    # E2E 测试运行器
│   ├── 打字机效果检测.py
│   └── 错误状态审计.py
└── reports/                     # 报告输出
    ├── markdown_report.py
    └── json_export.py
```

---

## 三、Prompt Tuning 工具

### 3.1 Prompt Registry（Prompt 注册表）

**目标**：将硬编码的 SYS_PROMPT 改为可配置、可版本化、可查询的结构。

**数据结构**：

```python
@dataclass
class PromptVariant:
    id: str
    system_prompt: str
    user_template: str  # jinja2 模板
    temperature: float
    max_tokens: int
    top_p: Optional[float] = None
    created_at: datetime
    tags: list[str] = field(default_factory=list)

@dataclass
class PromptEntry:
    divination_type: str
    variants: dict[str, PromptVariant]  # version_id -> variant
    active_variant: str
```

**功能**：
- `register_prompt(type, variant_id, prompt_text, params)` — 注册新 variant
- `activate_variant(type, variant_id)` — 切换活跃 variant
- `list_prompts()` — 列出所有 prompt 及状态
- `export_prompts()` — 导出为 JSON（可版本控制）
- `import_prompts(json)` — 从 JSON 导入

**文件**：`tools/prompt_tuning/prompt_registry.py`

---

### 3.2 Parameter Config（类型参数配置）

**目标**：支持不同占卜类型使用不同的 LLM 参数。

**配置结构**：

```python
PARAM_CONFIG = {
    "tarot": {"temperature": 0.9, "max_tokens": 1500},
    "birthday": {"temperature": 0.85, "max_tokens": 2000},
    "name": {"temperature": 0.8, "max_tokens": 800},
    "dream": {"temperature": 0.9, "max_tokens": 1200},
    "new_name": {"temperature": 0.85, "max_tokens": 1500},
    "plum_flower": {"temperature": 0.9, "max_tokens": 1000},
    "fate": {"temperature": 0.8, "max_tokens": 1000},  # fate 娱乐化可降低 temperature
}
```

**功能**：
- `get_params(divination_type)` — 获取指定类型的参数
- `override_params(type, overrides)` — 运行时覆盖
- `validate_params(params)` — 参数合法性校验（范围检查）

**文件**：`tools/prompt_tuning/param_config.py`

---

### 3.3 Prompt Evaluator（Prompt 效果评估器）

**目标**：不依赖人工判断，对 LLM 输出进行自动化质量评估。

**评估维度**：

| 维度 | 指标 | 判断方式 |
|------|------|----------|
| **完整性** | 是否被截断 | 检测 max_tokens 边界；检测结尾是否完整句子 |
| **相关性** | 是否回应了用户问题 | 关键词匹配（如 tarot 应提及"牌""塔罗"） |
| **角色一致性** | 是否符合角色设定 | prompt-specific 规则（如 fate 不应过于严肃） |
| **格式正确性** | 结构是否清晰 | 分段检测 / 列表检测 |
| **流畅度** | 语句是否通顺 | 句末标点完整率 |

**输出**：

```json
{
  "divination_type": "tarot",
  "prompt_variant_id": "v1.0",
  "timestamp": "2026-05-18T10:00:00Z",
  "scores": {
    "completeness": 0.85,
    "relevance": 0.92,
    "role_consistency": 0.88,
    "format_quality": 0.90,
    "fluency": 0.95
  },
  "overall_score": 0.90,
  "warnings": ["内容在句子中截断"],
  "raw_response_length": 850
}
```

**文件**：`tools/prompt_tuning/evaluator.py`

---

### 3.4 A/B Tester（A/B 测试框架）

**目标**：对不同 Prompt Variant 进行对比测试。

**功能**：
- `create_experiment(name, type, variant_ids)` — 创建实验
- `run_experiment(experiment_id, n_runs)` — 对每个 variant 运行 N 次
- `compare_results(experiment_id)` — 统计显著性检验（t-test）
- `export_report(experiment_id)` — 导出对比报告

**实验记录**：

```json
{
  "experiment_id": "exp_tarot_v1_vs_v2",
  "divination_type": "tarot",
  "variants": ["v1.0", "v2.0"],
  "runs_per_variant": 5,
  "results": {
    "v1.0": {"avg_completeness": 0.82, "avg_relevance": 0.88},
    "v2.0": {"avg_completeness": 0.91, "avg_relevance": 0.93}
  },
  "significance": {"p_value": 0.03, "significant": true}
}
```

**文件**：`tools/prompt_tuning/ab_tester.py`

---

## 四、流式输出诊断工具

### 4.1 SSE Parser（SSE 协议解析器）

**目标**：解析 SSE 流，检测协议层问题。

**功能**：
- `parse_sse_stream(raw_stream)` — 解析 SSE 流，返回 token 列表 + 元数据
- `detect_protocol_issues(stream)` — 检测格式问题：
  - 非 UTF-8 字符
  - 无效 JSON
  - 缺失 `data:` 前缀
  - 不一致的 `data:` 行格式
- `reassemble_tokens(tokens)` — 将 SSE data 重新组装为完整文本

**元数据**：

```json
{
  "total_tokens": 150,
  "total_bytes": 3240,
  "first_token_latency_ms": 230,
  "avg_token_interval_ms": 45,
  "last_token_timestamp": "...",
  "protocol_errors": [],
  "reassembled_text": "..."
}
```

**文件**：`tools/streaming_diagnostics/sse_parser.py`

---

### 4.2 完整性检测

**目标**：检测 LLM 输出是否在 max_tokens 边界被截断。

**检测方法**：

| 方法 | 描述 |
|------|------|
| **句子完整性** | 结尾是否为完整句子（以 `。！？.` 结尾） |
| **列表完整性** | 如果输出包含列表，检测是否以 `n/m` 格式结尾 |
| **结构完整性** | 如果输出包含代码块/表格，检测闭合标签 |
| **Token 上限逼近** | 实际 token 数接近 max_tokens 阈值 |

**输出**：

```json
{
  "is_complete": false,
  "completeness_score": 0.75,
  "cutoff_indicators": ["句子在中间被截断", "列表未完成 2/3"],
  "recommendation": "建议 max_tokens 从 1000 提升至 1500"
}
```

**文件**：`tools/streaming_diagnostics/完整性检测.py`

---

### 4.3 延迟分析

**目标**：诊断流式输出的时延问题。

**指标**：
- `time_to_first_token` — 首 token 响应时间
- `time_per_token` — 平均每 token 间隔
- `time_to_last_token` — 总输出时间
- `token_velocity` — token/秒 速率
- `inter_token_jitter` — token 间间隔标准差（稳定性指标）

**输出**：

```json
{
  "time_to_first_token_ms": 230,
  "avg_time_per_token_ms": 45,
  "token_velocity": 22.2,
  "inter_token_jitter_ms": 12,
  "total_output_time_ms": 6750,
  "verdict": "正常" | "偏慢" | "严重延迟"
}
```

**文件**：`tools/streaming_diagnostics/延迟分析.py`

---

## 五、交互体验测试工具

### 5.1 Playwright E2E Runner（Playwright 端到端测试运行器）

**目标**：用 Playwright 自动执行真实用户操作，测试 7 种占卜类型的完整交互流程。

**测试用例**：

```python
TEST_CASES = [
    {
        "name": "塔罗牌占卜 - 正常流程",
        "type": "tarot",
        "input": {"prompt": "最近工作运势如何？"},
        "expected": ["牌", "塔罗", "抽卡"],
    },
    {
        "name": "八字分析 - 生日格式验证",
        "type": "birthday",
        "input": {"birthday": "1990-01-01 08:00:00"},
        "expected": ["八字", "命理"],
    },
    {
        "name": "宝宝取名 - 参数完整性",
        "type": "new_name",
        "input": {"surname": "李", "sex": "male", "birthday": "2024-01-01"},
        "expected": ["名字", "李"],
    },
    # ... 7 cases total
]
```

**验证点**：
- 每个测试用例：发起请求 → 等待 SSE 完成 → 验证响应非空 → 验证内容包含关键词
- 测试完成后输出通过/失败统计

**文件**：`tools/interaction_testing/playwright_runner.py`

---

### 5.2 打字机效果检测

**目标**：验证前端 SSE 流的实时渲染效果。

**检测项**：

| 检测项 | 描述 |
|--------|------|
| **首次渲染延迟** | 第一个 token 到显示的时间 < 500ms |
| **渲染间隔抖动** | token 间渲染间隔标准差 < 100ms |
| **视觉连续性** | 页面无明显闪烁或跳变 |
| **流结束光标** | 流结束后光标正确处理（闪烁/消失） |
| **并发安全** | 快速连续点击"占卜"按钮时无渲染错乱 |

**实现**：使用 Playwright 截图 + 对比像素差异，或监听 DOM 变化事件。

**文件**：`tools/interaction_testing/打字机效果检测.py`

---

### 5.3 错误状态审计

**目标**：系统性地测试前端对各类错误状态的展示。

**测试场景**：

| 场景 | 模拟方式 |
|------|----------|
| 网络断开 | Playwright 断开网络 |
| API Key 无效 | 设置假的 API Key |
| 速率限制触发 | 快速发送 60+ 请求 |
| 服务器 500 | Mock 后端返回 500 |
| 空响应 | Mock 后端返回空 SSE |
| 流中途断开 | Mock 后端在第 10 个 token 后断开 |

**验证点**：
- 每种场景下前端是否显示明确的错误提示（非 500 server error 页面）
- 错误状态是否可清除、是否阻塞交互
- 错误消息是否对用户友好（不暴露内部细节）

**文件**：`tools/interaction_testing/错误状态审计.py`

---

## 六、报告生成工具

### 6.1 Markdown 报告生成器

**输出格式**：

```markdown
# Prompt Tuning 诊断报告

## 执行摘要
- 测试时间：2026-05-18 10:00 - 11:00
- 测试类型：7/7 占卜类型全覆盖
- 总体质量评分：0.87/1.0

## 各类型详细结果

### tarot
| Variant | 完整性 | 相关性 | 角色一致性 | 综合分 |
|---------|--------|--------|-----------|--------|
| v1.0 | 0.85 | 0.92 | 0.88 | 0.88 |
| v2.0 | 0.91 | 0.93 | 0.90 | 0.91 |
```

### 6.2 JSON 导出

支持 CI/CD 集成，将结果输出为机器可读格式。

---

## 七、执行计划

### ✅ 第一阶段：基础设施（已完成）
- [x] 创建 `tools/` 目录结构 → **直接复用 src/divination/base.py 实现**
- [x] 实现 `param_config.py` → ✅ 已实现为 `DIVINATION_PARAMS` 字典（见 `src/divination/base.py`）
- [x] 实现 `sse_parser.py` → ✅ SSE `[DONE]` 标识已在 `chatgpt_router.py` 实现

### ⏳ 第二阶段：评估能力（未实施，可选）
- [ ] 实现 `evaluator.py` — 5维度质量评估
- [ ] 实现 `完整性检测.py` — 截断检测
- [ ] 实现 `延迟分析.py` — 时延诊断

### ⏳ 第三阶段：交互测试（未实施，可选）
- [ ] 实现 `playwright_runner.py` — E2E 测试运行器
- [ ] 实现 `打字机效果检测.py`
- [ ] 实现 `错误状态审计.py`

### ⏳ 第四阶段：A/B 测试与报告（未实施，可选）
- [ ] 实现 `ab_tester.py`
- [ ] 实现 `markdown_report.py` 报告生成
- [ ] 实现 `json_export.py` CI 集成导出

### ⏳ 第五阶段：集成与迭代（持续）
- [ ] 对 7 种占卜类型执行全覆盖评估
- [ ] 根据评估结果调优 Prompt
- [ ] 建立 baseline，对每次 Prompt 修改做效果追踪

---

## 八、技术选型

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| HTTP 客户端 | `httpx` | 异步，支持流式响应 |
| SSE 解析 | 自研（已有参考实现） | 参考项目中 `test_minimax_stream.py` |
| 质量评估 | 正则 + 关键词 + 统计 | 不依赖额外 LLM |
| E2E 测试 | `playwright` | 跨浏览器，支持截图对比 |
| 统计检验 | `scipy` | t-test 显著性判断 |
| 报告导出 | `jinja2` | Markdown 模板渲染 |
| 配置管理 | `pydantic` | 配置校验 |

---

## 九、与 SELF_IMPROVEMENT_PLAN_v2 的衔接

本工具集服务于 **第5批（Prompt Tuning 框架建设）**：

| 计划项 | 状态 | 说明 |
|--------|------|------|
| `param_config.py` / `DIVINATION_PARAMS` | ✅ 已实现 | 见 `src/divination/base.py` |
| Prompt 参数化改造 | ✅ 已实现 | 7种类型差异化配置 |
| SSE 协议标准化（`[DONE]`） | ✅ 已实现 | 见 `chatgpt_router.py` |
| `prompt_registry.py` / `ab_tester.py` | ⏳ 未实施 | 可选，需 A/B 测试时实施 |
| `evaluator.py` / 流式输出质量评估 | ⏳ 未实施 | 可选，需量化效果时实施 |
| `打字机效果检测.py` / `错误状态审计.py` | ⏳ 未实施 | 可选，需自动化 E2E 时实施 |

工具集建设完成后，可系统性地对 7 种占卜类型的 Prompt 进行诊断和优化，并将优化结果反馈到 `src/divination/` 模块中。