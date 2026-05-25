# ChatGPT Tarot Divination 优化迭代计划

> 日期：2026-05-25
> 项目：`/Users/caowen/Documents/Codex/2026-05-25/infinity/chatgpt-tarot-divination`
> 范围：项目诊断、稳定性加固、用户体验优化、Prompt 质量提升、桌面端发布准备。

---

## 1. 诊断摘要

该项目是一个 AI 占卜产品，整体由 FastAPI 后端、React/Vite 前端和 Tauri 桌面壳组成。当前核心链路比较清晰：

1. 前端各占卜页面通过 `frontend/src/hooks/useDivination.ts` 提交用户输入。
2. 后端通过 `POST /api/divination` 接收请求。
3. `DivinationFactory` 根据占卜类型生成用户 prompt 与 system prompt。
4. 后端调用 OpenAI 兼容的 Chat Completions API，并开启流式输出。
5. SSE 数据块被转发给前端结果抽屉，同时写入本地历史记录。

项目已经具备较完整的产品基础：7 种占卜模式、流式输出、本地历史记录、自定义 API 设置、可选 GitHub OAuth、可配置缓存后端、Tauri 桌面端以及多份历史修复/迁移文档。下一阶段更适合聚焦在可复现运行、测试基线、安全边界、速率限制一致性、前端交互复用和 Prompt 质量评估上。

---

## 2. 当前健康状况

### 已确认

- 代码结构清晰，分为后端、前端、Tauri、文档、测试和部署配置。
- 后端测试文件已存在：`tests/test_cache.py`、`tests/test_divination.py`。
- 已有历史诊断和迁移资料，包括 `SELF_IMPROVEMENT_PLAN_v2.md`、`SELF_ITERATION_TEST_AND_INTERACTION_OPTIMIZATION_PLAN.md`、MiniMax 迁移计划等。
- 前端已具备基本工程化脚本：`build`、`build:tauri`、`preview`、`lint`。
- 当前 README 为中文，产品说明完整，但部分运行要求与代码实际约束不一致。

### 需要注意

- 当前工作区并非完全干净：`CHANGE-LOG.md` 已有修改，且本计划文档为新增/未跟踪文件。后续迭代时应避免覆盖这些已有变更。
- 实施 v0.2.0 前，README 仍写着 Python 3.8+，但代码已经使用 `list[str]`、`dict[str, ...]` 等 Python 3.9+ 泛型语法；v0.2.0 已将运行时契约更新为 Python 3.11。
- 部分历史计划里标记为“已修复”的问题，仍存在可继续加固空间，例如生产异常返回、默认 JWT 密钥策略、Tauri CSP、Upstash JSON 命令拼接等。

---

## 3. 高优先级问题

### H-1. Python 运行时契约不准确

实施 v0.2.0 前，README 写的是 Python 3.8+，但 `src/config.py` 等文件已经使用 Python 3.9+ 才支持的内建泛型语法，例如 `list[str]`。这会导致使用 Python 3.8 的开发者无法正常运行或收集测试。

**影响**

- 新开发者按 README 配置环境时容易失败。
- CI、Docker、本地 venv 的运行时版本可能不一致。
- 后续测试基线不稳定。

**建议**

- 将项目标准运行时统一到 Python 3.11。
- 增加 `.python-version` 或在 README 中明确 Python 版本。
- 同步更新 README、AGENTS、Docker/CI 文档和本地启动步骤。
- 如果确实要支持 Python 3.8，则需要把所有 `list[str]`、`tuple[...]`、`dict[...]` 改回 `typing.List`、`typing.Tuple`、`typing.Dict`，但这不建议作为主路线。

**v0.2.0 实施状态**

- 已新增 `.python-version`，将项目运行时声明为 Python 3.11。
- 已新增 `requirements-dev.txt`，纳入 pytest 测试运行器。
- 已新增 `.github/workflows/ci.yml`，在 PR 和 main push 上运行后端测试、前端 lint 与前端 build。
- 已更新 README、PROJECT_INFO、AGENTS 中的本地运行和测试说明。

---

### H-2. Redis / Upstash 速率限制存在并发计数偏差

`src/cache/redis_client.py` 使用当前秒级时间戳同时作为 sorted set 的 score 和 member。若同一秒内有多次请求，member 会互相覆盖，导致请求数被低估。`src/cache/upstash_kv_client.py` 的速率限制逻辑也有类似问题。

同时，内存后端使用 `req_count > max_requests` 才拒绝，而 Redis / Upstash 使用 `>= max_requests` 拒绝，三个缓存后端的边界语义不一致。

**影响**

- 高并发请求可能绕过限制。
- 不同缓存后端行为不同，部署环境切换后结果不可预测。
- 测试很难覆盖真实生产行为。

**建议**

- sorted set member 使用唯一值，例如 `{timestamp}:{uuid}`。
- 统一内存、Redis、Upstash 的拒绝条件。
- 增加边界测试：第 N 次允许、第 N+1 次拒绝。
- 增加同秒并发测试，确保不会因为 member 覆盖而漏计。

---

### H-3. 可选认证依赖占位 Token，匿名访问不够稳健

`src/user.py` 当前使用 `HTTPBearer()` 默认必填行为，而前端匿名请求会发送 `Bearer xxx` 作为占位值。后端业务逻辑虽然把 `xxx`、`undefined` 视为匿名，但没有 Authorization header 的 API 客户端可能在依赖层就被 FastAPI 拦截。

**影响**

- 匿名访问依赖前端特定实现，不够清晰。
- 第三方客户端或测试客户端若不传 Authorization header，可能得到非预期 403/401。
- “匿名用户”与“非法 token”语义混在一起。

**建议**

- 改为 `HTTPBearer(auto_error=False)`。
- 将缺失、空值、`xxx`、`undefined` 显式归类为匿名。
- 对无 token、占位 token、非法 token、过期 token、合法 token 增加测试。
- 前端可逐步停止发送占位 token，改为没有登录时不传 Authorization header。

---

### H-4. 生产异常响应泄露内部细节

`src/app.py` 的全局异常处理器会把 `str(exc)` 直接返回给客户端。

**影响**

- 第三方 API 错误、配置错误、堆栈上下文等内部信息可能暴露给用户。
- 前端无法稳定识别错误类型，只能展示原始后端文本。
- 生产环境安全边界不够清晰。

**建议**

- 客户端统一返回安全错误信封，例如 `{ "error": "internal_server_error", "message": "服务暂时不可用，请稍后重试" }`。
- 详细异常只写入服务端日志。
- 为常见业务错误增加稳定错误码，例如缺少 API key、速率限制、模型服务异常、参数错误。
- 前端根据错误码展示更友好的提示。

---

### H-5. 本地启动仍可能影响已有端口进程

`main.py` 曾经有自动清理 8000 端口占用的逻辑。虽然历史计划显示已经增加进程名校验，但自动结束端口进程本身仍然偏激进。

**影响**

- 开发者机器上可能有其他 Python、Node、Java、Uvicorn 服务占用同一端口。
- 自动 kill 会造成难以追踪的本地服务中断。

**建议**

- 默认行为改为检测端口占用并给出清晰提示。
- 如确实需要清理，提供显式参数，例如 `--kill-port`。
- README 从“自动清理 8000 端口占用”改为“端口占用时提示处理方式”。

---

## 4. 中优先级问题

### M-1. 前端占卜页面重复较多

7 个占卜页面重复了结果抽屉、加载按钮、提交状态、错误提示、布局容器等逻辑。

**建议**

- 抽取共享 `DivinationFormPage` 或 `DivinationPageShell`。
- 用类型化配置描述每种占卜模式的字段、默认值、校验规则和 payload 构造。
- 保留每种占卜的差异化体验，但把通用提交/展示流程收敛到一个地方。

---

### M-2. `useDivination` 职责过重

当前 hook 同时处理请求提交、SSE 解析、Markdown 渲染、历史记录、抽屉状态和错误提示。

**建议**

- 拆分为 `useDivinationStream`、`useDivinationResult`、`useDivinationHistory` 等更小单元。
- 将 `any` 参数替换为 TypeScript 判别联合类型。
- 明确区分网络错误、后端业务错误、模型服务错误和用户取消。

---

### M-3. Prompt 注入防御仍偏粗糙

当前项目已有输入清洗和 stop words 检查，但关键词阻断不是可靠的 prompt injection 防线，也可能误伤正常文本。

**建议**

- 继续保留长度、类型和结构化输入校验。
- 在 system prompt 中明确角色边界、输出边界和不可执行用户越权指令。
- 对用户输入进行结构化封装，而不是只拼接自然语言。
- 将关键词阻断降级为辅助信号，不作为主要安全策略。

---

### M-4. Tauri 发布安全配置需要加固

`src-tauri/tauri.conf.json` 中若仍保持宽松 CSP 或 `csp: null`，不适合直接发布桌面端。

**建议**

- 为桌面端增加明确 Content Security Policy。
- 限定本地 API、静态资源和外部跳转来源。
- 检查 sidecar 启停、端口冲突、日志输出和异常提示。

---

### M-5. CI 还没有覆盖常规 PR 健康检查

项目已有 Docker、CodeQL 等配置，但还需要一个普通的 PR CI 来证明基础质量。

**建议**

- 增加 `ci.yml`。
- 后端运行 `python -m pytest tests`。
- 前端运行 `pnpm install --frozen-lockfile`、`pnpm lint`、`pnpm build`。
- 可选增加 Docker build smoke test。

---

### M-6. Upstash 命令拼接方式不稳健

`src/cache/upstash_kv_client.py` 当前通过 f-string 手写 JSON 数组，一旦 key 或 token 含有引号、反斜杠等字符，就可能破坏 JSON 结构。

**建议**

- 使用 `json.dumps([...])` 或 `requests.post(..., json=[...])`。
- 为包含特殊字符的 key/token 增加测试。
- 对 `/multi-exec` 的响应结构做更明确的校验。

---

## 5. 版本化迭代路线图

### v0.2.0：运行时与测试基线

**目标**：让项目在本地和 CI 中可复现、可测试。

**范围**

- 统一 Python 运行时到 3.11。
- 将 README 和相关文档从 Python 3.8+ 更新为真实支持版本。
- 增加或明确测试命令。
- 确保测试依赖安装方式清楚可复现。
- 增加后端测试 CI。

**验收标准**

- 干净 Python 3.11 环境下 `python -m pytest tests` 通过。
- README 本地运行步骤可从新 clone 成功执行。
- CI 能在后端测试失败时阻断合并。

---

### v0.3.0：速率限制与认证正确性

**目标**：让请求限制和匿名/登录访问行为稳定可信。

**范围**

- 修复 Redis sorted set member 唯一性。
- 修复 Upstash member 唯一性和 JSON 命令序列化。
- 统一内存、Redis、Upstash 的限流边界语义。
- 将可选认证改为 `HTTPBearer(auto_error=False)`。
- 增加匿名访问、无 header、占位 token、非法 token、过期 token、合法 token 的测试。

**验收标准**

- 所有缓存后端采用同一套限流语义。
- 同秒并发请求不会被覆盖漏计。
- 不带 Authorization header 的请求能进入匿名流程。

**v0.3.0 实施状态**

- 已将可选认证改为 `HTTPBearer(auto_error=False)`，缺失、空值、`xxx`、`undefined`、`null` token 均进入匿名流程。
- 已移除前端匿名请求中的 `Bearer xxx` 占位头，仅在存在 JWT 时发送 Authorization。
- 已为 Redis / Upstash 限流写入唯一请求 member，避免同秒请求互相覆盖。
- 已统一内存、Redis、Upstash 的限流边界：第 N 次请求允许，第 N+1 次拒绝。
- 已将 Upstash 命令改为 `requests.post(..., json=...)`，避免手写 JSON 字符串导致特殊字符破坏协议。
- 已增加限流和认证测试，覆盖匿名、占位 token、非法 token、过期 token、合法 token，以及 Redis / Upstash 同秒计数。

---

### v0.4.0：生产安全加固

**目标**：减少敏感信息泄露和不安全默认值。

**范围**

- 将全局异常响应改为安全错误信封。
- 详细异常仅保留在服务端日志。
- 生产环境禁止默认 `jwt_secret=secret`，除非显式声明开发模式。
- 检查 CORS 默认值和部署示例。
- 从 `docker-compose.yaml` / README 示例中移除容易误用的不安全默认密钥。

**验收标准**

- 客户端 500 响应不暴露原始异常文本。
- 生产配置缺少安全密钥时有明确失败模式。
- 部署文档不再鼓励不安全默认配置。

**v0.4.0 实施状态**

- 已将全局异常响应改为稳定错误信封，客户端不再收到原始异常文本。
- 已将 OpenAI 兼容服务调用错误和流式输出错误改为生产安全错误码/消息，详细异常只写入服务端日志。
- 已新增 `app_env` 配置；当 `app_env=production` 且 `jwt_secret=secret` 时启动失败。
- 已更新 Docker Compose 和 README 部署示例，生产部署必须显式提供 `JWT_SECRET`，并建议配置生产域名 CORS。
- 已更新环境变量文档，标明 `jwt_secret` 的开发默认值不能用于生产。
- 已增加生产密钥校验和全局异常响应测试。

---

### v0.5.0：前端交互重构

**目标**：减少重复 UI 代码，提升错误处理和使用体验。

**范围**

- 抽取共享占卜页面壳和提交按钮组。
- 为 7 种占卜模式定义类型化请求 payload。
- 拆分流式请求、Markdown 渲染和历史保存逻辑。
- 针对缺少 API key、速率限制、网络失败、模型服务错误展示不同提示。
- 增加结果操作：复制、重试、查看历史。

**验收标准**

- 7 个占卜页面共享统一流程，同时保留各自字段差异。
- TypeScript 能发现错误 payload。
- 用户看到的是可操作错误提示，而不是原始后端文本。

**v0.5.0 实施状态**

- 已新增 `DivinationFormPage`，统一页面标题、提交按钮、查看结果按钮和结果抽屉接入。
- 已新增 `frontend/src/types/divination.ts`，为 7 种占卜模式定义类型化 payload。
- 已新增 `frontend/src/services/divinationStream.ts`，将 SSE 请求和错误解析从 React hook 中拆出。
- 已新增 `useDivinationHistory`，将历史保存逻辑从 `useDivination` 中拆出。
- 已精简 7 个占卜页面，页面只保留字段状态、局部校验和 payload 构造。
- 已为结果抽屉增加复制、重试、查看历史操作。
- 已细化前端错误消息：速率限制、API 配置缺失、服务端错误、网络异常、模型服务错误均有独立提示路径。

---

### v0.6.0：Prompt 注册表与质量评估

**目标**：让 Prompt 变更可版本化、可评估、可回滚。

**范围**

- 将 prompt 文本和模型参数移入版本化注册表。
- 为每种占卜模式准备代表性样例输入。
- 增加轻量输出检查：完整性、相关性、结构、角色一致性。
- 准备 OpenAI、MiniMax、自定义 API 的 provider profile。
- 为高风险 prompt 改动生成对比报告。

**验收标准**

- 不改路由代码也能比较不同 prompt variant。
- 每种占卜模式都有基础评估样例。
- Provider 差异和参数差异有明确文档。

**v0.6.0 实施状态**

- 已新增 `src/divination/prompt_registry.py`，集中管理 7 种占卜类型的 active prompt variant、system prompt、temperature、max_tokens、tags、说明和评估样例。
- 已将 7 个占卜工厂改为从 Prompt Registry 读取 system prompt。
- 已将 `DivinationFactory.get_params()` 改为从 Prompt Registry 读取 active variant 参数。
- 已新增 provider profiles：`openai`、`minimax`、`custom`，记录 OpenAI-compatible provider 差异。
- 已新增 `tuning/backend/prompt_evaluator.py`，提供完整性、相关性、角色一致性、结构质量、流畅度的本地轻量评分。
- 已更新 `tuning/runner.py`、`tuning/backend/test_prompts.py` 和 `tuning/backend/prompts/templates.py`，调优工具复用同一份注册表和评估样例。
- 已新增 `tests/test_prompt_registry.py`，覆盖注册表、工厂接入、评估器和 provider profiles。

---

### v0.7.0：Tauri 发布准备

**目标**：让桌面端具备更可靠、更安全的发布条件。

**范围**

- 增加 Tauri CSP。
- 加固 Python sidecar 的启动、关闭和错误提示。
- 改进本地端口冲突处理。
- 检查桌面构建配置、图标、环境变量读取和日志输出。

**验收标准**

- 桌面端启动失败时能给出清楚原因。
- 安全配置适合发布版本。
- 本地 API 和前端资源加载都在明确策略下工作。

---

## 6. 建议执行顺序

建议先从 **v0.2.0** 开始。运行时与测试基线是后续所有优化的地基：如果项目无法在统一环境中稳定启动和测试，后续的限流、安全、前端重构都会缺少可靠反馈。

完成 v0.2.0 后，优先进入 **v0.3.0**。速率限制和认证会直接影响线上正确性与服务信任度，且修复范围相对集中，适合作为第二步。

第三步建议推进 **v0.4.0**，把生产错误响应、默认密钥、CORS 和部署示例一起收口。之后再进入前端重构、Prompt 评估和桌面端发布准备。

---

## 7. 第一轮落地清单

第一轮建议控制在 1 到 2 天内完成，目标是先让项目“能稳定验证”：

- 更新 README 的 Python 版本要求和本地运行步骤。
- 增加 `.python-version`，推荐 `3.11`。
- 确认 `pytest` 依赖和测试命令。
- 新增基础 CI：后端测试、前端 lint、前端 build。
- 修复或记录当前测试失败项。
- 将本计划中 v0.2.0 的验收标准作为第一轮完成标准。

完成第一轮后，再进入限流和认证修复会更稳。
