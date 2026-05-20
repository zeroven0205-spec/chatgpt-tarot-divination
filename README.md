# AI 占卜

基于 GPT 的智能占卜平台，支持塔罗牌、八字、姓名、周公解梦、宝宝取名、梅花易数、姻缘配对七种占卜服务。

![demo](assets/demo.png)

---

## 功能列表

| 占卜类型 | 说明 |
|---------|------|
| 塔罗牌占卜 | 虚拟抽卡，解读内心困惑与未来可能 |
| 生辰八字 | 基于出生时间分析命理运势 |
| 姓名五格 | 姓名笔画与五行性格分析 |
| 周公解梦 | 梦境解析，探索潜意识信息 |
| 宝宝取名 | 结合八字五行推荐吉祥名字 |
| 梅花易数 | 传统易学数字占卜 |
| 姻缘占卜 | 两人姓名缘分与婚恋分析 |

**特色功能**：
- 流式输出 — AI 结果实时以打字机效果呈现
- 历史记录 — 每种占卜类型自动保存最近 10 条
- 响应式设计 — 适配手机、平板、电脑
- 暗色模式 — 明暗主题自由切换
- 自定义 API — 支持接入自己的 API Key 和 Base URL
- MiniMax / OpenAI 多后端支持

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI 0.115.7 + Uvicorn |
| 前端框架 | React 18 + Vite 6 + TypeScript |
| 状态管理 | Zustand 5（持久化到 localStorage） |
| 样式 | Tailwind CSS 3 + shadcn/ui |
| 动画 | Framer Motion 12 |
| AI 集成 | OpenAI Python Client 1.60.0 |
| 认证 | GitHub OAuth + JWT |
| 桌面端 | Tauri 2.0（Rust + Python Sidecar） |
| 缓存 | 内存 / Redis / Upstash KV（可选） |

---

## 项目结构

```
chatgpt-tarot-divination/
├── src/                          # FastAPI 后端
│   ├── app.py                     # 应用入口
│   ├── config.py                  # 配置管理
│   ├── models.py                  # Pydantic 模型
│   ├── chatgpt_router.py          # 占卜 API 路由
│   ├── user_router.py            # 用户/认证路由
│   ├── limiter.py                # 速率限制
│   ├── divination/               # 占卜模块（工厂模式）
│   │   ├── base.py               # DivinationFactory 元类
│   │   ├── tarot.py              # 塔罗牌
│   │   ├── birthday.py           # 八字
│   │   ├── name.py              # 姓名五格
│   │   ├── dream.py             # 周公解梦
│   │   ├── new_name.py          # 宝宝取名
│   │   ├── plum_flower.py       # 梅花易数
│   │   └── fate.py              # 姻缘配对
│   └── cache/                    # 缓存客户端
├── frontend/                     # React + Vite 前端
│   └── src/
│       ├── App.tsx              # 主组件
│       ├── store/               # Zustand 状态
│       ├── hooks/               # 自定义 Hooks
│       ├── pages/               # 页面组件
│       └── components/          # 通用组件
├── src-tauri/                   # Tauri 桌面配置
├── main.py                      # 后端入口
├── requirements.txt             # Python 依赖
└── docker-compose.yaml         # Docker 配置
```

---

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/divination` | POST | 占卜主接口（流式 SSE） |
| `/api/v1/settings` | GET | 应用配置查询 |
| `/api/v1/login` | GET | GitHub OAuth 登录跳转 |
| `/api/v1/oauth` | POST | GitHub OAuth 回调 |
| `/health` | GET | 健康检查 |

**自定义 API 配置**：通过请求头覆盖后端配置

```
x-api-key: <your-api-key>
x-api-url: <your-api-base-url>
x-api-model: <your-model-name>
```

---

## 部署方式

### 方式一：Vercel 部署（推荐）

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fzeroven0205-spec%2Fchatgpt-tarot-divination&env=api_key,api_base&project-name=ai-divination&repository-name=ai-divination&demo-title=AI%20Divination&demo-description=AI%20Divination&demo-url=https%3A%2F%2Fdivination.app.awsl.uk)

环境变量：`api_key`（必填）、`api_base`（可选）

### 方式二：Docker 部署

```yaml
services:
  chatgpt-tarot-divination:
    image: ghcr.io/zeroven0205-spec/chatgpt-tarot-divination:latest
    container_name: chatgpt-tarot-divination
    restart: always
    ports:
      - 8000:8000
    environment:
      - api_key=sk-xxx                         # 必填
      # - api_base=https://api.openai.com/v1   # 可选
      # - model=gpt-3.5-turbo                   # 可选
      # - github_client_id=xxx                   # 可选：GitHub OAuth
      # - github_client_secret=xxx              # 可选
      # - jwt_secret=secret                      # 可选
      # - rate_limit=60,3600                     # 可选：游客速率限制
      # - user_rate_limit=600,3600               # 可选：用户速率限制
```

```bash
docker-compose up -d
# 访问 http://localhost:8000
```

### 方式三：本地运行

**前置要求**：Node.js 16+ / Python 3.8+ / pnpm

```bash
# 1. 配置环境变量
echo "api_key=sk-xxxx" > .env

# 2. 前端构建
cd frontend && pnpm install && pnpm build --emptyOutDir && cd ..

# 3. 部署前端文件
rm -rf dist && cp -r frontend/dist/ dist

# 4. 安装后端依赖
python3 -m venv ./venv
./venv/bin/python3 -m pip install -r requirements.txt

# 5. 启动后端（自动清理 8000 端口占用）
./venv/bin/python3 main.py
# 访问 http://localhost:8000
```

### 方式四：Tauri 桌面应用（macOS / Windows）

```bash
# 需先完成方式三的前端构建步骤
cd src-tauri && cargo build --release
# 构建产物在 src-tauri/target/release/ 下
```

---

## 环境变量配置

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | 是 | — | OpenAI / MiniMax API Key |
| `api_base` | 否 | `https://api.openai.com/v1` | API Base URL |
| `model` | 否 | `gpt-3.5-turbo` | 默认模型 |
| `github_client_id` | 否 | — | GitHub OAuth Client ID |
| `github_client_secret` | 否 | — | GitHub OAuth Secret |
| `jwt_secret` | 否 | `secret` | JWT 签名密钥 |
| `rate_limit` | 否 | `60,3600` | 游客速率限制（请求数,秒） |
| `user_rate_limit` | 否 | `600,3600` | 用户速率限制 |

---

## 速率限制

| 用户类型 | 默认限制 |
|---------|---------|
| 游客（未认证） | 60 请求 / 小时（按 IP） |
| 登录用户 | 600 请求 / 小时（按用户名） |

支持切换缓存后端：`cache_client_type=memory | redis | upstash`

---

## License

MIT License
