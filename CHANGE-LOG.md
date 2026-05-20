# Change Log

All notable changes to this project are documented in this file.

## [1.1.0] - 2026-05-18

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