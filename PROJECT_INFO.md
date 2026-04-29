# AI Tarot Divination - AI 占卜

多功能 AI 算命占卜平台，支持塔罗牌、八字、姓名、周公解梦、宝宝取名、梅花易数、姻缘配对七种占卜服务。

---

## 项目概述

**AI Tarot Divination** 是一款基于 ChatGPT/OpenAI API 的中文网页应用，提供多种传统占卜服务。用户可以选择不同的占卜方式，输入相关问题或信息，系统将实时流式返回 AI 生成的分析结果。

### 核心功能

| 占卜类型 | 标识 | 说明 |
|---------|------|------|
| 塔罗牌 | `tarot` | 虚拟塔罗牌占卜，随机抽取3张牌 |
| 八字测算 | `birthday` | 根据出生时间进行八字命理分析 |
| 姓名五格 | `name` | 姓名笔画与五行分析 |
| 周公解梦 | `dream` | 梦境解读与分析 |
| 宝宝取名 | `new_name` | 结合八字五行的起名建议 |
| 梅花易数 | `plum_flower` | 传统梅花易数，两数占卜 |
| 姻缘配对 | `fate` | 两人姓名缘分分析 |

### 技术特性

- **流式响应** — Server-Sent Events (SSE) 实现打字机效果，实时展示 AI 输出
- **历史记录** — 本地 localStorage 存储最近 10 条记录
- **自定义 API** — 用户可在设置页填写自己的 OpenAI API Key / Base URL / Model
- **GitHub OAuth** — 用户认证系统，支持 JWT Token
- **速率限制** — 支持内存 / Redis / Upstash KV 三种后端
- **响应式设计** — 适配移动端，深色模式支持
- **桌面应用** — 可通过 Tauri 构建为 macOS / Windows 原生应用

---

## 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.115.7 | Web 框架 |
| Uvicorn | 0.34.0 | ASGI 服务器 |
| OpenAI Python | 1.60.0 | GPT API 调用 |
| PyJWT | 2.10.1 | JWT 认证 |
| Pydantic | 2.10.6 | 数据校验 |
| httpx | 0.27.0 | HTTP 客户端 |
| cachetools | 5.5.2 | 内存缓存 |
| redis | 5.2.1 | 分布式缓存（可选） |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.3.1 | UI 框架 |
| Vite | 6.0.1 | 构建工具 |
| React Router | 6.28.0 | 路由 |
| Zustand | 5.0.9 | 状态管理 |
| Tailwind CSS | 3.4.15 | 样式 |
| shadcn/ui | — | UI 组件库 |
| Framer Motion | 12.23.26 | 动画 |
| markdown-it | 14.1.0 | Markdown 渲染 |
| lunar-javascript | 1.7.6 | 农历转换 |
| Lucide React | 0.460.0 | 图标 |

### 桌面

| 技术 | 说明 |
|------|------|
| Tauri 2.0 | Rust 编写的桌面框架，Python sidecar 运行于端口 12333 |

---

## 项目结构

```
chatgpt-tarot-divination/
├── src/                          # FastAPI 后端源码
│   ├── app.py                     # FastAPI 应用主入口
│   ├── config.py                  # 配置加载
│   ├── models.py                 # Pydantic 请求/响应模型
│   ├── chatgpt_router.py          # 占卜 API 路由
│   ├── user_router.py            # 用户/认证路由
│   ├── user.py                   # 用户认证逻辑
│   ├── limiter.py                # 速率限制
│   ├── divination/               # 占卜模块（工厂模式）
│   │   ├── base.py               # DivinationFactory 元类
│   │   ├── tarot.py              # 塔罗牌
│   │   ├── birthday.py           # 八字
│   │   ├── name.py               # 姓名五格
│   │   ├── dream.py             # 周公解梦
│   │   ├── new_name.py          # 宝宝取名
│   │   ├── plum_flower.py       # 梅花易数
│   │   └── fate.py              # 姻缘配对
│   └── cache/                    # 缓存客户端（工厂模式）
│       ├── base.py              # CacheClientBase 元类
│       ├── cache_client_factory.py
│       ├── memory_client.py     # 内存缓存
│       ├── redis_client.py      # Redis 缓存
│       └── upstash_kv_client.py # Upstash KV
├── frontend/                     # React + Vite 前端
│   ├── src/
│   │   ├── App.tsx              # 主组件
│   │   ├── main.tsx             # 入口
│   │   ├── store/index.ts       # Zustand 全局状态
│   │   ├── hooks/
│   │   │   ├── useDivination.ts # 占卜请求 Hook（SSE 流式）
│   │   │   └── index.ts         # useIsMobile, useLocalStorage
│   │   ├── pages/
│   │   │   ├── Market.tsx       # 首页（占卜选择）
│   │   │   ├── Login.tsx         # GitHub OAuth 登录
│   │   │   ├── Settings.tsx     # API 配置
│   │   │   ├── History.tsx      # 历史记录
│   │   │   └── divination/      # 各占卜类型页面
│   │   ├── components/          # 通用组件
│   │   ├── layouts/             # 布局组件
│   │   └── config/constants.ts  # 占卜选项配置
│   └── package.json
├── src-tauri/                   # Tauri 桌面配置
├── main.py                      # 后端入口（开发）
├── main-tauri.py                # Tauri sidecar 入口
├── requirements.txt             # Python 依赖
└── docker-compose.yaml         # Docker 部署
```

---

## API 设计

### `POST /api/divination` — 占卜主接口（流式）

**请求体** (`DivinationBody`)：

```json
{
  "prompt": "最近工作运势如何？",
  "prompt_type": "tarot"
}
```

可选字段：

```json
{
  "birthday": "1990-01-01 08:00",      // 八字占卜
  "new_name": {                          // 宝宝取名
    "surname": "李",
    "sex": "male",
    "birthday": "2024-01-01",
    "new_name_prompt": "希望宝宝聪明健康"
  },
  "plum_flower": { "num1": 8, "num2": 3 },  // 梅花易数
  "fate": { "name1": "小明", "name2": "小红" }  // 姻缘配对
}
```

**响应**：SSE 流式

```
data: {"content":"今"}

data: {"content":"今天"}

data: {"content":"今天的"}
...
```

**请求头（可选）**：

| 请求头 | 说明 |
|--------|------|
| `Authorization: Bearer <jwt>` | JWT 认证 |
| `x-api-key` | 自定义 API Key |
| `x-api-url` | 自定义 API Base URL |
| `x-api-model` | 自定义模型名称 |

### `GET /api/v1/settings` — 应用设置

返回当前应用配置、速率限制、广告配置等。

```json
{
  "login_type": "github",
  "enable_login": true,
  "enable_rate_limit": true,
  "default_api_base": "https://api.openai.com/v1",
  "default_model": "gpt-3.5-turbo"
}
```

### `GET /api/v1/login?login_type=github&redirect_url=<url>` — GitHub OAuth 登录

返回 GitHub 授权跳转 URL。

### `POST /api/v1/oauth` — OAuth 回调

接收 GitHub 授权码，返回 JWT Token。

### `GET /health` — 健康检查

返回 `"ok"`。

---

## 数据存储

应用**不依赖传统数据库**，采用以下存储方案：

| 场景 | 存储方式 |
|------|---------|
| 速率限制计数 | 内存（cachetools）/ Redis / Upstash KV |
| 前端历史记录 | localStorage（每种占卜类型最多 10 条） |
| 用户偏好 | localStorage（Zustand persist） |
| 用户认证 | JWT Token（前端 localStorage 存储） |

---

## 配置与环境变量

### 后端 `.env`

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | 是 | — | OpenAI API Key |
| `api_base` | 否 | `https://api.openai.com/v1` | API Base URL |
| `model` | 否 | `gpt-3.5-turbo` | 默认模型 |
| `github_client_id` | 否 | — | GitHub OAuth Client ID |
| `github_client_secret` | 否 | — | GitHub OAuth Client Secret |
| `jwt_secret` | 否 | `secret` | JWT 签名密钥 |
| `redis_url` | 否 | — | Redis 连接地址 |
| `upstash_api_url` | 否 | — | Upstash KV REST URL |
| `upstash_api_token` | 否 | — | Upstash KV Token |
| `rate_limit` | 否 | `60,3600` | 游客速率限制（请求数,秒） |
| `user_rate_limit` | 否 | `600,3600` | 用户速率限制 |
| `enable_rate_limit` | 否 | `true` | 是否启用速率限制 |

### 前端 `.env`

| 变量 | 说明 |
|------|------|
| `VITE_API_BASE` | API 基础地址（空 = 同源） |
| `VITE_IS_TAURI` | 是否运行在 Tauri 桌面应用中 |

---

## 本地运行

### 前提条件

- Node.js 16+
- Python 3.8+
- pnpm
- OpenAI API Key

### 后端启动

```bash
# 创建虚拟环境
python3 -m venv ./venv

# 安装依赖
./venv/bin/python3 -m pip install -r requirements.txt

# 配置环境变量
echo "api_key=sk-xxxx" > .env

# 启动后端
./venv/bin/python3 main.py
```

后端地址：`http://localhost:8000`

### 前端启动

```bash
cd frontend
pnpm install
pnpm dev
```

前端地址：`http://localhost:5173`

### 生产构建

```bash
cd frontend
pnpm build --emptyOutDir

# 将前端构建产物复制到后端 dist 目录
cd ..
rm -rf dist
cp -r frontend/dist/ dist

# 启动生产服务
./venv/bin/python3 main.py
```

### Docker 部署

```bash
docker-compose up -d
```

---

## 架构模式

### 占卜工厂模式（MetaDivination 元类）

所有占卜类型通过 `DivinationFactory` 元类自动注册到 `divination_map`，新增占卜类型只需继承 `BaseDivination` 并设置 `divination_type` 属性：

```python
class MetaDivination(type):
    divination_map = {}

    def __init__(cls, name, bases, attrs):
        if hasattr(cls, 'divination_type'):
            MetaDivination.divination_map[cls.divination_type] = cls
```

### 缓存客户端工厂（MetaCacheClient 元类）

支持内存 / Redis / Upstash KV 三种缓存后端，通过环境变量切换。

### 流式响应

FastAPI `StreamingResponse` + 异步生成器透传 OpenAI 流式输出，前端使用 `@microsoft/fetch-event-source` 接收 SSE 事件。

### 状态管理

Zustand + persist 中间件，将主题偏好、JWT Token、自定义 API 配置等持久化到 localStorage。

---

## 速率限制

| 用户类型 | 默认限制 |
|---------|---------|
| 游客（未认证） | 60 请求 / 小时（按 IP） |
| 登录用户 | 600 请求 / 小时（按用户名） |

速率限制数据默认存储在内存中，分布式部署时可切换为 Redis 或 Upstash KV。
