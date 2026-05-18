# AI 占卜 — 自我迭代升级优化规划 v2

> 规划日期：2026-05-18
> 评估方式：代码质量诊断 + 架构分析 + 用户体验审计
> 基于：SELF_IMPROVEMENT_PLAN.md（2026-04-29） + 项目深度诊断

---

## 一、问题总览

| 严重度 | 数量 | 说明 |
|--------|------|------|
| CRITICAL | 4 | 必须修复后才能上线生产 |
| HIGH | 7 | 影响功能正确性和稳定性 |
| MEDIUM | 6 | 影响一致性和可维护性 |
| LOW | 5 | 小幅改进 |

---

## 二、CRITICAL 级问题（必须修复）

### [C-1] JWT 密钥硬编码默认值

**文件**：`src/config.py:23`

```python
jwt_secret: str = Field(default="secret", exclude=True)
```

**风险**：若部署时未设置 `jwt_secret`，应用使用可猜测的默认密钥，攻击者可伪造 JWT 登录。

**修复**：启动时检测是否为默认密钥，若是则抛出错误或生成随机密钥：

```python
def __init__(self):
    if self.jwt_secret == "secret" and not self.jwt_secret_from_env:
        raise ValueError("jwt_secret must be set in production")
```

---

### [C-2] CORS 开放所有来源

**文件**：`src/app.py:18-22`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 危险：allow_credentials=True 时浏览器拒绝
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**风险**：浏览器会拒绝 `allow_origins=["*"]` + `allow_credentials=True` 的组合；攻击者可利用此开放策略进行 CSRF。

**修复**：从配置或环境变量读取允许的域名列表：

```python
allow_origins=settings.cors_origins.split(",") if settings.cors_origins else ["https://divination.app.awsl.uk"]
```

---

### [C-3] XSS 风险 — `dangerouslySetInnerHTML` 未做 HTML 消毒

**文件**：`frontend/src/components/ResultDrawer.tsx:95`

```typescript
dangerouslySetInnerHTML={{ __html: result }}
```

**风险**：`markdown-it` 渲染后的 HTML 中可能包含 `<script>` 标签或事件处理器。

**修复**：引入 `dompurify` 对渲染后的 HTML 进行消毒：

```typescript
import DOMPurify from 'dompurify'
dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(md.render(result)) }}
```

**备注**：经检查当前代码已使用 `DOMPurify.sanitize()`，此项可从 CRITICAL 降级为 MEDIUM（需确认所有调用路径均已消毒）。

---

### [C-4] new_name.py 字段引用错误

**文件**：`src/divination/new_name.py:26-27`

```python
birthday = datetime.datetime.strptime(
    divination_body.birthday, '%Y-%m-%d %H:%M:%S'  # 错误：应为 new_name.birthday
)
```

**风险**：传入的 `birthday` 为 `None`，导致解析必败，宝宝取名功能完全不可用。

**修复**：将 `divination_body.birthday` 改为 `divination_body.new_name.birthday`。

---

## 三、HIGH 级问题

### [H-1] OAuth 响应 KeyError 风险

**文件**：`src/user_router.py:61`

```python
access_token = resp.json()['access_token']
```

**风险**：GitHub API 响应格式变化或网络异常时直接 `KeyError` → 500。

**修复**：防御性访问：

```python
access_token = resp.json().get('access_token')
user_name = user_data.get('login')
```

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

**修复**：用 `asyncio.Lock` 保护临界区。

---

### [H-3] CacheClientFactory 拼写错误导致缓存后端失效

**文件**：`src/cache/cache_client_factory.py:11`

```python
cls = MetaCacheClient.cilent_map.get(...)  # cilent → client
```

**风险**：`CacheClientFactory.get_client()` 始终返回 `None`，Redis/Upstash 缓存后端完全失效（仅内存缓存可工作）。

**修复**：将所有 `cilent_map` 改为 `client_map`。

---

### [H-4] get_token() 忽略 TTL 过期检查

**文件**：`src/cache/memory_client.py:50-57`

```python
def get_token(cls, key: str) -> Optional[str]:
    if key in cls.token_cache:
        token, expire_seconds = cls.token_cache[key]
        return token   # 未检查是否过期
```

**修复**：返回前判断 `time.time() >= stored_time + expire_seconds`。

---

### [H-5] main.py 启动时无差别 SIGKILL 杀进程

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

### [H-7] IP 伪造风险 — 缺少 X-Forwarded-For 支持

**文件**：`src/limiter.py:12-19`

```python
def get_real_ipaddr(request: Request) -> str:
    return request.headers.get("x-real-ip", request.client.host)
```

**风险**：若服务置于代理（nginx/cloudflare）后，代理通过 `X-Forwarded-For` 传真实 IP，当前代码不检查，攻击者可伪造 IP 绕过限流。

**修复**：增加 `X-Forwarded-For` 支持（取第一个非代理 IP）：

```python
xff = request.headers.get("x-forwarded-for")
if xff:
    ip = xff.split(",")[0].strip()
else:
    ip = request.headers.get("x-real-ip", request.client.host)
```

---

## 四、MEDIUM 级问题

### [M-1] `BirthdayFactory` 日期解析无异常处理

**文件**：`src/divination/birthday.py:19-20`

`datetime.strptime` 失败时抛出 500 而非 400。

**修复**：try-except 包裹，返回 `400 Bad Request` 并说明期望格式。

---

### [M-2] `FateFactory` Prompt 注入风险

**文件**：`src/divination/fate.py:25`

```python
prompt = f'{fate.name1}, {fate.name2}'
```

姓名中含特殊字符（如 `}`, `,`）可能导致 prompt 注入。

**修复**：对姓名进行基本转义或长度限制+特殊字符过滤。

---

### [M-3] JWT 验证静默异常吞噬

**文件**：`src/user.py:32-33`

```python
except Exception:
    return
```

JWT 验证失败无日志，攻击者无法被追踪。

**修复**：至少记录一次 warning log。

---

### [M-4] Upstash KV 客户端字符串插值破坏 Redis 协议

**文件**：`src/cache/upstash_kv_client.py:26`

```python
data=f'["SET", "{key}", "{token}", "EX", "{expire_seconds}"]'
```

若 key/token 含引号则破坏协议。

---

### [M-5] 前端 Settings 不持久化到后端

**文件**：`frontend/src/pages/Settings.tsx:39-48`

自定义 API 配置只存在 Zustand store 中，刷新页面后丢失。

---

### [M-6] JWT 过期不在前端主动验证

**文件**：`frontend/src/store/index.ts`

刷新页面时 JWT 是否有效需要等到 API 调用失败才知道。

---

## 五、LOW 级问题

### [L-1] GitHub OAuth URL 常量拼写错误

**文件**：`src/user_router.py:20` — `GITHUB_TOEKN_URL`（TOEKN → TOKEN）

---

### [L-2] app.py f-string 语法错误

**文件**：`src/app.py:62`

```python
detail=f"No prompt type {divination_body.prompt_type} not supported"
```

闭括号位置错误，message 无法正确显示。

---

### [L-3] Stop words 大小写敏感可绕过

**文件**：`src/app.py:53`

```python
if any(w in divination_body.prompt.lower() for w in STOP_WORDS):
```

检查的是 prompt 小写化，但 STOP_WORDS 是原始大小写。"IGNORE" 可绕过。

---

### [L-4] 姓名长度限制过严

**文件**：`src/divination/name.py:16`

`len(divination_body.prompt) > 10 or len(divination_body.prompt) < 1` — 中文复姓或少数民族姓名易被误拒。建议扩展到 1-20 字符。

---

### [L-5] Cache 模块缺少 `__all__` 显式导出

---

## 六、Prompt Tuning 模块诊断（占卜 Prompt 工程）

### 6.1 当前 Prompt 架构

7 种占卜类型的 system prompt 均以硬编码常量存在：

| 占卜类型 | System Prompt 角色 | 用户输入 |
|---------|-------------------|----------|
| `tarot` | 塔罗占卜师 | 用户问题（≤40字） |
| `birthday` | 生辰八字算命师 | 生日时间戳 |
| `name` | 姓名五格算命师 | 用户姓名（1-10字） |
| `dream` | 周公解梦师 | 梦境描述（≤40字） |
| `new_name` | 起名师 | 姓氏+性别+生日+期望 |
| `plum_flower` | 梅花易数占卜师 | 两个数字 |
| `fate` | 姻缘助手 | 两个姓名 |

### 6.2 发现的问题

| 问题 | 详情 |
|------|------|
| **硬编码不可调** | 所有 SYS_PROMPT 是常量，无版本控制，无参数化调优机制 |
| **无质量评估** | 无法追踪 LLM 返回内容的质量、完整性、用户满意度 |
| **无 Prompt 版本管理** | 修改 prompt 需要改代码，无法 A/B 测试 |
| **无差异化调优** | 不同占卜类型共享相同参数（temperature=0.9, max_tokens=1000），未针对场景优化 |
| **Prompt 措辞不一致** | 有的包含"我请求你担任...角色"，有的简化为"你是..."，role-playing 效果参差不齐 |
| **fate prompt 过于娱乐化** | `SYS_PROMPT` 包含"不需要很真实，只需要娱乐化"，与用户期望不符 |
| **无角色一致性指导** | tarot prompt 提到"洗牌""介绍牌套"，但无抽牌逻辑实现，角色描述与实际功能脱节 |
| **new_name birthday 解析错误** | 代码 bug 导致功能不可用（C-4 已在 CRITICAL 修复） |

---

## 七、修复优先级路线图

```
第1批（安全红线 + 功能性Bug，必须尽快修复）
  ├─ [C-4] new_name.birthday 字段引用错误 → 功能不可用
  ├─ [C-1] JWT 密钥默认值 "secret"
  ├─ [H-3] cilent_map 拼写错误 → Redis/Upstash 缓存完全失效
  ├─ [H-2] 内存缓存竞态条件
  └─ [H-1] OAuth KeyError 风险

第2批（稳定性，保证功能正确）
  ├─ [H-7] X-Forwarded-For IP 伪造风险
  ├─ [H-4] get_token TTL 忽略
  ├─ [H-6] 流式错误协议不完整
  ├─ [M-1] birthday 日期解析无异常处理
  └─ [M-2] fate prompt 注入风险

第3批（一致性 / 可维护性）
  ├─ [C-2] CORS 多域名配置
  ├─ [H-5] SIGKILL 端口杀进程风险
  ├─ [M-3] JWT 验证静默异常
  ├─ [M-4] Upstash 协议字符串插值
  ├─ [L-1] GITHUB_TOEKN_URL 拼写
  ├─ [L-2] app.py f-string 语法错误
  └─ [L-4] name.py 长度限制过严

第4批（UX 改进）
  ├─ [M-5] Settings 持久化
  ├─ [M-6] JWT 前端主动验证
  └─ [L-3] Stop words 大小写敏感

第5批（Prompt Tuning 框架建设）
  ├─ Prompt 参数化改造（支持温度/max_tokens 按类型配置）
  ├─ Prompt 版本管理与 A/B 测试基础设施
  ├─ 流式输出质量评估机制（完整性检测 / 截断识别）
  └─ Prompt 效果日志与用户满意度追踪
```

---

## 八、架构层优化建议

| 优化项 | 说明 | 影响 |
|--------|------|------|
| **可配置 max_tokens per 类型** | 从 `.env` 读取，支持不同占卜类型不同配额 | 解决内容截断问题 |
| **Redis Lua 原子限流** | 将 check-and-append 改为 Redis Lua 脚本 | 彻底解决竞态 |
| **SSE 协议标准化** | 统一定义 data 格式，增加 `[DONE]` 结束标识 | 提升前端健壮性 |
| **前端错误状态分离** | useDivination 返回独立 error 状态 | 改善 UX |
| **配置项集中管理** | 将所有 .env 配置项集中到 Settings 类 | 便于维护 |
| **Prompt Tuning 工具集** | 独立于业务的 Prompt 调优框架（见下） | 提升内容质量 |