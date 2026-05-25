# Change Log

All notable changes to this project are documented in this file.

## [0.6.0] - 2026-05-25

### Added

- **Prompt Registry** — 新增 `src/divination/prompt_registry.py`。
  - 集中管理 7 种占卜类型的 active prompt variant。
  - 将 system prompt、temperature、max_tokens、tags、note 和评估样例统一放入注册表。
  - 提供 `get_system_prompt()`、`get_params()`、`get_evaluation_fixtures()`、`export_prompt_registry()` 等访问入口。

- **Provider Profiles** — 在 Prompt Registry 中声明 provider profile 元数据。
  - 包含 `openai`、`minimax`、`custom`。
  - 当前用于记录 OpenAI-compatible provider 差异，不改变现有请求链路。

- **Prompt Evaluator** — 新增 `tuning/backend/prompt_evaluator.py`。
  - 本地轻量评估输出质量，不依赖额外模型调用。
  - 评分维度包括 completeness、relevance、role_consistency、format_quality、fluency。

- **Prompt Registry tests** — 新增 `tests/test_prompt_registry.py`。
  - 覆盖注册表完整性、active variant、LLM 参数、评估样例、工厂读取注册表、provider profile 和评估器输出。

### Changed

- **Business prompt source** — 7 个 `src/divination/*.py` 工厂改为从 Prompt Registry 读取 system prompt。
  - `DivinationFactory.get_params()` 改为读取 Prompt Registry 中 active variant 的模型参数。
  - 后续 prompt 变更可以先新增 variant，再切换 active variant。

- **Tuning tools** — 调优脚本复用同一份 Prompt Registry。
  - `tuning/backend/test_prompts.py` 和 `tuning/runner.py` 使用 registry 中的 evaluation fixtures。
  - 修正旧 tuning 默认输入与当前 Pydantic 模型不一致的问题。
  - `tuning/backend/prompts/templates.py` 改为导出 registry 快照。
  - `tuning/README.md` 更新 Prompt Registry、Prompt Evaluator 和 Provider Profiles 说明。

---

## [0.5.0] - 2026-05-25

### Changed

- **Shared divination page shell** — 新增 `frontend/src/components/DivinationFormPage.tsx`。
  - 统一 7 个占卜页面的标题、提交按钮、查看结果按钮和结果抽屉接入方式。
  - `TarotPage`、`BirthdayPage`、`NewNamePage`、`NamePage`、`DreamPage`、`PlumFlowerPage`、`FatePage` 只保留各自字段、状态和 payload 构造逻辑。

- **Typed divination payloads** — 新增 `frontend/src/types/divination.ts`。
  - 为 7 种占卜模式定义判别类型和 payload map。
  - `useDivination` 与共享页面壳按占卜类型约束提交 payload。

- **Streaming request separation** — 新增 `frontend/src/services/divinationStream.ts`。
  - 将 SSE 请求、响应打开、chunk 解析、后端错误对象识别从 React hook 中拆出。
  - 区分速率限制、API 配置缺失、服务端错误、网络异常和模型服务错误提示。

- **History persistence separation** — 新增 `frontend/src/hooks/useDivinationHistory.ts`。
  - 将占卜结果历史保存逻辑从 `useDivination` 中拆出。

### Added

- **Result actions** — `ResultDrawer` 增加结果操作。
  - 复制结果。
  - 重新占卜。
  - 查看历史。

### Fixed

- **Streaming error handling** — 前端现在能识别 `{ error, message }` 形式的流式错误对象，并进入错误提示路径。

---

## [0.4.0] - 2026-05-25

### Security

- **Production error hardening** — 全局异常响应不再向客户端暴露原始异常文本。
  - `src/app.py` 的 500 响应改为稳定错误信封：`internal_server_error` + 用户友好提示。
  - 服务端仍保留详细异常日志，便于排查问题。

- **AI provider error hardening** — 模型服务和流式输出异常改为生产安全错误码。
  - `src/chatgpt_router.py` 中 OpenAI 兼容服务调用失败返回 `ai_provider_error`。
  - SSE 流式中断返回 `streaming_error`，不再把底层异常文本发送给前端。
  - `frontend/src/hooks/useDivination.ts` 支持识别流式错误对象并进入错误处理路径。

- **JWT production guard** — 新增生产环境 JWT 密钥强制校验。
  - `src/config.py` 新增 `app_env`，默认 `development`。
  - 当 `app_env=production` 且 `jwt_secret=secret` 时启动失败。
  - 开发环境仍可使用默认值，但会输出 warning。

### Changed

- **Deployment examples** — 生产部署示例不再鼓励不安全默认密钥。
  - `docker-compose.yaml` 改为通过 `${JWT_SECRET:?Set JWT_SECRET}` 显式要求生产 JWT 密钥。
  - README / PROJECT_INFO 增加 `app_env`、`cors_origins`、生产 JWT 密钥说明。
  - Docker Compose 示例增加生产域名 CORS 配置提示。

### Added

- **`tests/test_security.py`** — 覆盖生产安全加固行为。
  - 生产环境默认 `jwt_secret=secret` 会失败。
  - 生产环境强密钥可通过配置。
  - 全局异常处理器不会泄露原始异常文本。

---

## [0.3.0] - 2026-05-25

### Fixed

- **Rate limit member uniqueness** — 修复 Redis / Upstash 同秒请求覆盖导致的限流漏计。
  - `src/cache/redis_client.py` 使用 `{timestamp}:{uuid}` 作为 sorted set member。
  - `src/cache/upstash_kv_client.py` 同样使用唯一 member，避免高并发下覆盖计数。

- **Rate limit boundary consistency** — 统一内存、Redis、Upstash 的限流边界语义。
  - 第 N 次请求允许，第 N+1 次请求拒绝。
  - 内存后端窗口过期边界与 Redis / Upstash 对齐。

- **Optional authentication** — 匿名访问不再依赖占位 Authorization header。
  - `src/user.py` 改为 `HTTPBearer(auto_error=False)`。
  - 缺失、空值、`xxx`、`undefined`、`null` token 均进入匿名流程。
  - 非法 token、过期 token 回落匿名，不阻断匿名请求链路。

### Changed

- **Upstash request serialization** — Upstash REST 命令改用 `requests.post(..., json=...)`。
  - 避免 key/token 中引号、反斜杠等特殊字符破坏手写 JSON 字符串。
  - `/multi-exec` 响应结构增加显式校验。

- **Frontend auth headers** — 前端匿名请求不再发送 `Bearer xxx`。
  - `frontend/src/App.tsx` 和 `frontend/src/hooks/useDivination.ts` 仅在存在 JWT 时设置 Authorization。

### Added

- **Rate limit tests** — 扩展 `tests/test_cache.py`。
  - Redis 同秒多请求计数测试。
  - Upstash 同秒多请求计数测试。
  - Upstash token 命令 JSON 序列化测试。

- **Authentication tests** — 新增 `tests/test_user.py`。
  - 覆盖无凭证、占位 token、非法 token、过期 token、合法 token。

---

## [0.2.0] - 2026-05-25

### Added

- **Python runtime baseline** — 新增 `.python-version`，声明项目运行时为 Python 3.11。
- **Development test dependencies** — 新增 `requirements-dev.txt`。
  - 复用 `requirements.txt`。
  - 加入 `pytest==8.3.4` 作为后端测试运行器。

- **CI workflow** — 新增 `.github/workflows/ci.yml`。
  - PR / main push 时运行后端测试：`python -m pytest tests`。
  - 前端运行 `pnpm lint` 和 `pnpm build`。
  - CI 使用 Python 3.11、Node.js 20、pnpm 10.10.0。

### Changed

- **Documentation runtime requirements** — README / PROJECT_INFO / AGENTS 同步运行时要求。
  - Python 从 3.8+ 更新为 3.11。
  - Node.js 从 16+ 更新为 20+。
  - pnpm 明确为 10+。

- **Local test instructions** — README / PROJECT_INFO / AGENTS 增加后端测试命令。
  - `python3.11 -m venv ./venv`
  - `./venv/bin/python3 -m pip install -r requirements-dev.txt`
  - `./venv/bin/python3 -m pytest tests`

### Note

- 本地验证环境仅有 Python 3.8.5，无法执行 Python 3.11 基线测试；测试应在 Python 3.11 venv 或 CI 中运行。

---

## [0.1.0] - 2026-05-18

### Fixed

- **[C-5]** `src/divination/fate.py:21-22` — 姻缘预测参数验证改进
  - 新增 `name1`/`name2` 字段空值检查（原仅检查 `fate` 对象是否存在）
  - 错误信息更新为中文：`"姻缘预测需要提供两个人的姓名 (name1 和 name2)"`

- **[C-6]** `tuning/backend/test_api.py:35,37` — 测试 payload 字段结构修正
  - `new_name`: 改为嵌套对象 `{"surname", "sex", "birthday", "new_name_prompt"}`
  - `fate`: 改为嵌套对象 `{"name1", "name2"}`
  - 与 `src/models.py` 中 `DivinationBody` 的 Pydantic 模型定义保持一致

- **[C-4]** `src/divination/new_name.py:26-27` — `birthday` 字段引用错误
  - `divination_body.birthday` → `divination_body.new_name.birthday`（原始终为 None，导致宝宝取名功能完全不可用）
  - 同步修正校验逻辑：`new_name.birthday` 加入 `all()` 条件
  - 新增日期格式错误处理：`strptime` 失败返回 400 而非 500

- **[H-2]** `src/cache/memory_client.py:60-90` — 速率限制竞态条件
  - 引入 `threading.Lock` 类级别锁 `_rate_limit_lock`
  - `check_rate_limit` 全程 read-modify-write 操作包裹在锁中
  - 修复异常处理：不再吞掉 `HTTPException`（原 `except Exception` 内置 `isinstance` 判断导致 429 状态码被误吞）

### Added

- **`tests/test_divination.py`** — 6 个单元测试覆盖 new_name 模块
  - `test_new_name_build_prompt_success` — 有效输入验证
  - `test_new_name_birthday_parsing` — birthday 字段正确解析
  - `test_new_name_missing_birthday` — 缺失字段 Pydantic 层报错
  - `test_new_name_invalid_birthday_format` — 无效格式返回 400
  - `test_new_name_missing_surname` — 空姓氏返回 400
  - `test_new_name_prompt_too_long` — new_name_prompt 超长返回 400

- **`tests/test_cache.py`** — 4 个单元测试覆盖 memory_client 竞态修复
  - `test_rate_limit_basic` — 阈值内放行
  - `test_rate_limit_exceeded` — 超阈值返回 429
  - `test_rate_limit_concurrent` — 15 并发/10 限制下恰好 5 次拒绝（并发计数正确性）
  - `test_rate_limit_lock_exists` — `threading.Lock` 存在性验证

### Note

- **`src/cache/cache_client_factory.py`** — 经搜索确认 `cilent_map` 拼写错误在当前代码中**不存在**（已使用正确的 `client_map`），此问题可忽略，无需修复。
