# AI 占卜 — 自我迭代升级优化规划

> 规划日期：2026-04-29
> 评估方式：三路 Agent 并行诊断（代码质量 / 架构性能 / 功能 UX）

---

## 一、问题总览

| 严重度 | 数量 | 说明 |
|--------|------|------|
| CRITICAL | 3 | 必须修复后才能上线生产 |
| HIGH | 6 | 影响功能正确性和稳定性 |
| MEDIUM | 5 | 影响一致性和可维护性 |
| LOW | 3 | 小幅改进 |

---

## 二、CRITICAL 级问题（必须修复）

### [C-1] CORS 开放所有来源

**文件**：`src/app.py:18-22`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 危险：允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**风险**：浏览器会拒绝 `allow_origins=["*"]` + `allow_credentials=True` 的组合；攻击者可利用此开放策略进行 CSRF。

**修复方案**：从配置或环境变量读取允许的域名列表：

```python
allow_origins=settings.cors_origins.split(",") if settings.cors_origins else ["https://divination.app.awsl.uk"]
```

---

### [C-2] JWT 密钥硬编码默认值

**文件**：`src/config.py:23`

```python
jwt_secret: str = Field(default="secret", exclude=True)
```

**风险**：若部署时未设置 `jwt_secret`，应用使用可猜测的默认密钥，攻击者可伪造 JWT 登录。

**修复方案**：启动时检测是否为默认密钥，若是则抛出错误或生成随机密钥：

```python
def __init__(self):
    if self.jwt_secret == "secret" and not self.jwt_secret_from_env:
        raise ValueError("jwt_secret must be set in production")
```

---

### [C-3] XSS 风险 — `dangerouslySetInnerHTML` 未做 HTML 消毒

**文件**：`frontend/src/components/ResultDrawer.tsx:95`

```typescript
dangerouslySetInnerHTML={{ __html: result }}
```

**风险**：LLM 返回内容经过 `markdown-it` 渲染后直接作为 HTML 嵌入，`markdown-it` 不消毒 HTML。攻击者可注入 `<script>` 标签。

**修复方案**：引入 `dompurify` 对渲染后的 HTML 进行消毒：

```typescript
import DOMPurify from 'dompurify'
// ...
dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(md.render(result)) }}
```

---

## 三、HIGH 级问题

### [H-1] `max_tokens=1000` 过小导致响应截断

**文件**：`src/chatgpt_router.py:86`

生辰八字和姓名五格分析内容较长，1000 tokens 会截断在句子中间，导致输出不完整。

**修复**：改为 2000，或从 `settings` 配置项读取。

---

### [H-2] 速率限制器竞态条件（非原子读写）

**文件**：`src/cache/memory_client.py:64-76`

```python
history = cls.request_limit_map[key]       # read
while history and history[0] < ...:
    history.pop(0)                          # modify shared list
history.append(cur_timestamp)
cls.request_limit_map[key] = history       # write
```

**风险**：并发请求时两个协程交替读写同一 key 的 list，导致计数错误。

**修复**：用 `threading.Lock` 或 `asyncio.Lock` 保护临界区。

---

### [H-3] `CacheClientFactory.get_client()` 因拼写错误永远返回 None

**文件**：`src/cache/cache_client_factory.py:11`

```python
cls = MetaCacheClient.cilent_map.get(...)  # cilent → client
```

**风险**：由于 `cilent_map` 拼写错误，`CacheClientFactory.get_client()` 始终返回 `None`。所有依赖此方法的速率限制检查静默失效（无限制通过）。

**修复**：将所有 `cilent_map` 改为 `client_map`。

---

### [H-4] `get_token()` 忽略 TTL 过期检查

**文件**：`src/cache/memory_client.py:50-57`

```python
def get_token(cls, key: str) -> Optional[str]:
    if key in cls.token_cache:
        token, expire_seconds = cls.token_cache[key]
        return token   # 未检查是否过期
```

**修复**：返回前判断 `time.time() >= stored_time + expire_seconds`。

---

### [H-5] `main.py` 启动时无差别 SIGKILL 杀进程

**文件**：`main.py:24-36`

```python
subprocess.run(["kill", "-9", pid], check=False)  # 杀掉所有占用端口的进程
```

**风险**：端口 8000 被任何无关进程占用时会被强制终止。

**修复**：增加 `--force` 标志确认，或验证进程名为 uvicorn/python 再杀。

---

### [H-6] 流式错误处理协议不完整

**文件**：`src/chatgpt_router.py:105-115`

流中途出错时返回的 SSE 格式与正常 token 不同，前端无法区分是部分成功还是错误。

**修复**：统一 SSE 协议，始终返回 `{"content":"..."}` 或 `{"error":"..."}`，流结束时发送 `data: [DONE]`。

---

## 四、MEDIUM 级问题

### [M-1] `NewNameFactory` 字段引用不一致

**文件**：`src/divination/new_name.py:21,27`

验证用 `divination_body.new_name.birthday`，解析用 `divination_body.birthday`。前端同时传两个字段使工作正常，但代码逻辑不一致。

---

### [M-2] 速率限制超限时不返回标准 Header

**文件**：`src/limiter.py` / `src/chatgpt_router.py`

建议返回 `X-RateLimit-Remaining`、`Retry-After` 等标准 Header。

---

### [M-3] 前端 Settings 不持久化到后端

**文件**：`frontend/src/pages/Settings.tsx:39-48`

自定义 API 配置只存在 Zustand store 中，刷新页面后丢失。

---

### [M-4] JWT 过期不在前端主动验证

**文件**：`frontend/src/store/index.ts` / `frontend/src/App.tsx`

刷新页面时 JWT 是否有效需要等到 API 调用失败才知道。

---

### [M-5] 历史记录清空效率低

**文件**：`frontend/src/pages/History.tsx:42-49`

逐条删除而非调用 `clearHistory()`，产生 N 次 localStorage 读写。

---

## 五、LOW 级问题

### [L-1] GitHub OAuth URL 常量拼写错误

**文件**：`src/user_router.py:20` — `GITHUB_TOEKN_URL`（TOEKN 应为 TOKEN）

### [L-2] `chatgpt_router.py` 未使用的 Import

**文件**：`src/chatgpt_router.py:7` — `APIRouter` 直接使用未显式标注类型

### [L-3] Cache 模块缺少 `__all__` 显式导出

---

## 六、修复优先级路线图

```
第1批（安全红线，必须尽快修复）
  └─ [C-2] JWT 密钥默认值为 "secret"
  └─ [C-3] dangerouslySetInnerHTML XSS
  └─ [H-3] cilent_map 拼写错误导致 rate limit 失效

第2批（稳定性，保证功能正确）
  └─ [H-1] max_tokens=1000 响应截断
  └─ [H-2] 速率限制竞态条件
  └─ [H-4] get_token TTL 忽略
  └─ [H-6] 流式错误协议不完整

第3批（一致性 / 可维护性）
  └─ [C-1] CORS 开放所有来源
  └─ [H-5] SIGKILL 端口杀进程风险
  └─ [M-1] NewNameFactory 字段不一致
  └─ [L-1] GITHUB_TOEKN_URL 拼写错误

第4批（UX 改进）
  └─ [M-2] 速率限制 Header
  └─ [M-3] Settings 持久化
  └─ [M-4] JWT 前端主动验证
  └─ [M-5] History 清空优化
```

---

## 七、架构层优化建议

| 优化项 | 说明 | 影响 |
|--------|------|------|
| **可配置 max_tokens** | 从 `.env` 读取，支持不同占卜类型不同配额 | 解决截断问题 |
| **Redis Lua 原子限流** | 将 check-and-append 改为 Redis Lua 脚本 | 彻底解决竞态 |
| **SSE 协议标准化** | 统一定义 data 格式，增加 `[DONE]` 结束标识 | 提升前端健壮性 |
| **前端错误状态分离** | useDivination 返回独立 error 状态 | 改善 UX |
| **配置项集中管理** | 将所有 .env 配置项集中到 Settings 类 | 便于维护 |
