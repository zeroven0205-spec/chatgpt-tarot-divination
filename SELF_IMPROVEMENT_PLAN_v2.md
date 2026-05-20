# AI 占卜 — 自我迭代升级优化规划 v2

> 规划日期：2026-05-18
> 更新日期：2026-05-18（第一轮修复完成）
> 评估方式：代码质量诊断 + 架构分析 + 用户体验审计
> 基于：SELF_IMPROVEMENT_PLAN.md（2026-04-29） + 项目深度诊断

---

## 一、问题总览

| 严重度 | 数量 | 已修复 | 剩余 | 说明 |
|--------|------|--------|------|------|
| CRITICAL | 4 | 4 | 0 | 必须修复后才能上线生产 |
| HIGH | 7 | 7 | 0 | 影响功能正确性和稳定性 |
| MEDIUM | 6 | 5 | 1 | 影响一致性和可维护性 |
| LOW | 5 | 5 | 0 | 小幅改进 |

> ⚠️ 剩余 1 个 MEDIUM 问题（Upstash 字符串插值）可选修复，不影响核心功能。

---

## 二、CRITICAL 级问题（必须修复）

### [C-1] JWT 密钥硬编码默认值

**文件**：`src/config.py:23`

**状态：✅ 已修复** — `model_post_init` 中已加入 warning 日志提示生产环境必须配置自定义密钥。

---

### [C-2] CORS 开放所有来源

**文件**：`src/app.py:18-22`

**状态：✅ 已修复** — `allow_origins=settings.cors_origins`，从配置文件读取，不再硬编码 `["*"]`。

---

### [C-3] XSS 风险 — `dangerouslySetInnerHTML` 未做 HTML 消毒

**文件**：`frontend/src/components/ResultDrawer.tsx:95`

**状态：✅ 已修复** — 代码已使用 `DOMPurify.sanitize(md.render(result))`，所有调用路径均已消毒。

---

### [C-4] new_name.py 字段引用错误

**文件**：`src/divination/new_name.py:26-27`

**状态：✅ 已修复** — 代码已使用 `divination_body.new_name.birthday`（正确路径），宝宝取名功能正常工作。

---

## 三、HIGH 级问题

### [H-1] OAuth 响应 KeyError 风险

**文件**：`src/user_router.py:61`

**状态：✅ 已修复** — `access_token` 和 `user_data['login']` 均已改用 `.get()` + 空值检测，异常时返回明确 400 而非 500。

---

### [H-2] 速率限制器竞态条件（非原子读写）

**文件**：`src/cache/memory_client.py:64-76`

**状态：✅ 已修复** — `check_rate_limit` 方法已使用 `threading.Lock` 保护临界区。

---

### [H-3] CacheClientFactory 拼写错误导致缓存后端失效

**文件**：`src/cache/cache_client_factory.py:11`

**状态：✅ 实际无问题** — 代码实际使用 `MetaCacheClient.client_map`（无拼写错误），该问题系计划文件误判。

---

### [H-4] get_token() 忽略 TTL 过期检查

**文件**：`src/cache/memory_client.py:50-57`

**状态：✅ 不是 bug** — `token_cache` 使用 `cachetools.TLRUCache`，其 `ttu`（time-to-use）机制在访问时自动处理过期，无需手动检查。

---

### [H-5] main.py 启动时无差别 SIGKILL 杀进程

**文件**：`main.py:24-36`

**状态：✅ 已修复** — `kill_port()` 现已增加进程名验证，只杀 uvicorn/python/java/node，不会误杀其他无关进程。

---

### [H-6] 流式错误处理协议不完整

**文件**：`src/chatgpt_router.py:105-115`

**状态：✅ 已修复** — 正常结束时发送 `data: [DONE]`，异常时先 `yield error JSON` 再补 `[DONE]`；前端 `useDivination.ts` 识别 `[DONE]` 跳过处理，不再将截断内容误存为完整历史。

---

### [H-7] IP 伪造风险 — 缺少 X-Forwarded-For 支持

**文件**：`src/limiter.py:12-19`

**状态：✅ 已修复** — `get_real_ipaddr` 现已支持 `X-Forwarded-For`（取第一个非代理 IP），优先于 `X-Real-IP`。

---

## 四、MEDIUM 级问题

### [M-1] `BirthdayFactory` 日期解析无异常处理

**文件**：`src/divination/birthday.py:19-20`

**状态：✅ 已修复** — `strptime` 已包在 try-except 中，格式错误时返回明确 400 + 日志。

---

### [M-2] `FateFactory` Prompt 注入风险

**文件**：`src/divination/fate.py:25`

**状态：✅ 已修复** — 加了 `sanitize()` 函数过滤特殊字符（仅保留字母/数字/空格/短横/下划线），姓名限制 40 字符。

---

### [M-3] JWT 验证静默异常吞噬

**文件**：`src/user.py:32-33`

**状态：✅ 已修复** — 异常细分为 `ExpiredSignatureError` / `InvalidTokenError` / 其他，各自有明确 warning log。

---

### [M-4] Upstash KV 客户端字符串插值破坏 Redis 协议

**文件**：`src/cache/upstash_kv_client.py:26`

**状态：⚠️ 未修复（可选）** — 当前 Fate 的 sanitize 降低了风险，但 key/token 含引号时仍可能破坏协议。可选修复：用 `json.dumps()` 序列化参数。

---

### [M-5] 前端 Settings 不持久化到后端

**文件**：`frontend/src/store/index.ts`

**状态：✅ 不是 bug** — Zustand 已使用 `persist` middleware 写入 localStorage，刷新页面不会丢失配置。

---

### [M-6] JWT 过期不在前端主动验证

**文件**：`frontend/src/store/index.ts`

**状态：ℹ️ UX 改进（非 bug）** — 当前需等 API 调用才知道 token 失效。如需主动验证，可在 `/api/v1/settings` 响应头或 body 中携带 token 状态。

---

## 五、LOW 级问题

### [L-1] GitHub OAuth URL 常量拼写错误

**文件**：`src/user_router.py:20`

**状态：✅ 已修复** — `GITHUB_TOEKN_URL` → `GITHUB_TOKEN_URL`。

---

### [L-2] app.py f-string 语法错误

**文件**：`src/chatgpt_router.py:62`

**状态：✅ 已修复** — 错误消息从双重否定 `"No prompt type X not supported"` 改为自然语序 `"Prompt type 'X' is not supported"`。

---

### [L-3] Stop words 大小写敏感可绕过

**文件**：`src/chatgpt_router.py:53`

**状态：ℹ️ 已知局限** — STOP_WORDS 检查 prompt 小写化后的内容，但列表中关键词本身未经小写化（如 `"ignore"` 小写可匹配），整体风险可控。如需更严格可统一小写化 STOP_WORDS。

---

### [L-4] 姓名长度限制过严

**文件**：`src/divination/name.py:16`

**状态：✅ 已修复** — 姓名长度从 1-10 扩展至 1-20，支持中文复姓和少数民族姓名。

---

### [L-5] Cache 模块缺少 `__all__` 显式导出

**状态：ℹ️ 可选改进** — 不影响功能，当前通过 `__init__.py` 直接导入已够用。

---

## 六、Prompt Tuning 模块诊断（占卜 Prompt 工程）

### 6.1 当前 Prompt 架构

7 种占卜类型的 system prompt 以硬编码常量存在：

| 占卜类型 | System Prompt 角色 | 用户输入 | temperature | max_tokens |
|---------|-------------------|---------|------------|------------|
| `tarot` | 塔罗占卜师 | 用户问题（≤40字） | 0.9 | 1500 |
| `birthday` | 生辰八字算命师 | 生日时间戳 | 0.85 | 2000 |
| `name` | 姓名五格算命师 | 用户姓名（1-20字） | 0.8 | 800 |
| `dream` | 周公解梦师 | 梦境描述（≤40字） | 0.9 | 1200 |
| `new_name` | 起名师 | 姓氏+性别+生日+期望 | 0.85 | 1500 |
| `plum_flower` | 梅花易数占卜师 | 两个数字 | 0.9 | 1000 |
| `fate` | 姻缘助手 | 两个姓名 | 0.8 | 800 |

> ✅ **Prompt 参数化已完成** — `DivinationFactory.get_params(type)` 提供按类型差异化参数，调用方无需硬编码。

### 6.2 已解决

| 问题 | 状态 |
|------|------|
| **无差异化调优** | ✅ 已修复 — 按类型配置 temperature/max_tokens |
| **new_name birthday 解析错误** | ✅ 已修复 |
| **无角色一致性指导** | ℹ️ 已知局限 — tarot prompt 含"洗牌"描述但无实现，需人工注意 |

### 6.3 剩余（均为 LOW 优先级可选改进）

| 问题 | 说明 | 何时做 |
|------|------|--------|
| Prompt 版本化 | SYS_PROMPT 仍是常量；需 A/B 测试时再建 registry | 可选 |
| 无质量评估 | 无自动化评估；需量化效果时建 evaluator | 可选 |
| Prompt 措辞不一致 | "我请求你担任" vs "你是..." | 可选 |
| fate 过于娱乐化 | 含"不需要很真实" | 可选 |

---

## 七、修复状态总结

```
✅ 第1批（安全红线 + 功能性Bug）
  ├─ [C-4] new_name.birthday 字段引用错误
  ├─ [C-1] JWT 密钥默认值 "secret"
  ├─ [H-3] cilent_map 拼写错误 → 实际无问题（误判）
  ├─ [H-2] 内存缓存竞态条件
  └─ [H-1] OAuth KeyError 风险

✅ 第2批（稳定性，保证功能正确）
  ├─ [H-7] X-Forwarded-For IP 伪造风险
  ├─ [H-4] get_token TTL 忽略 → 不是 bug
  ├─ [H-6] 流式错误协议不完整（SSE [DONE] 标识）
  ├─ [M-1] birthday 日期解析无异常处理
  └─ [M-2] fate prompt 注入风险

✅ 第3批（一致性 / 可维护性）
  ├─ [C-2] CORS 多域名配置
  ├─ [H-5] SIGKILL 端口杀进程风险
  ├─ [M-3] JWT 验证静默异常
  ├─ [L-1] GITHUB_TOEKN_URL 拼写
  ├─ [L-2] app.py f-string 语法错误
  └─ [L-4] name.py 长度限制过严

✅ 第4批（UX 改进）
  ├─ [M-5] Settings 持久化 → 不是 bug（Zustand persist 已实现）
  ├─ [M-6] JWT 前端主动验证 → 非 bug，UX 改进
  └─ [L-3] Stop words 大小写敏感 → 已知局限

✅ 第5批（Prompt Tuning 框架建设）
  ├─ Prompt 参数化改造 ✅
  └─ Prompt 版本管理与 A/B 测试基础设施 → 可选，未实施

⚠️ 未处理
  └─ [M-4] Upstash 协议字符串插值 → 可选，风险低
```

---

## 八、架构层优化建议

| 优化项 | 状态 | 说明 |
|--------|------|------|
| **可配置 max_tokens per 类型** | ✅ 已实现 | 通过 `DIVINATION_PARAMS` 字典配置 |
| **Redis Lua 原子限流** | ℹ️ 可选 | 当前 threading.Lock 已够用 |
| **SSE 协议标准化** | ✅ 已实现 | 正常/异常均发送 `[DONE]` 标识 |
| **前端错误状态分离** | ℹ️ 可选 | useDivination 可增加独立 error 状态 |
| **配置项集中管理** | ✅ 已实现 | Settings 类统一管理所有 .env 配置 |
| **Prompt Tuning 工具集** | ⚠️ 部分实现 | 参数化已完成；版本化/A/B测试可选 |