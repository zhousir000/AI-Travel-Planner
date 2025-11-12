# AI Travel Planner （AI 智能旅行规划系统）

借助语音输入与大语言模型自动生成行程计划、预算建议，并支持多终端同步管理旅行数据。本项目使用 Python（FastAPI）构建后端，同时提供内置前端界面，满足课程关于 AI 行程规划、费用管理、用户登录、语音功能、地图展示、Docker 发布以及 PDF 提交的要求。

## ✨ 核心特性

- **语音 / 文字输入**：支持浏览器 Web Speech API 或科大讯飞 API（可选），快速捕捉旅行需求。
- **AI 行程生成**：集成 LLM 客户端（默认 Mock，可切换至阿里云 DashScope 或 OpenAI），生成包含交通/景点/餐饮的日程与预算。
- **费用预算与管理**：对接行程计划后即可添加日常开销，系统自动汇总统计。
- **用户系统与云端同步**：JWT 鉴权，行程计划持久化存储，支持多份计划管理。
- **地图展示**：嵌入高德地图，直观查看每日打卡地点（需自备 Key）。
- **Docker 化部署 & CI/CD**：提供 Dockerfile、docker-compose 以及 GitHub Actions（自动构建并推送到阿里云镜像仓库）。
- **PDF 提交**：内置脚本可生成包含 GitHub 仓库地址与 README 内容的 submission.pdf。

## 🏗️ 技术栈

- **后端**：FastAPI、SQLAlchemy (Async)、Pydantic Settings、JWT (python-jose)、Passlib
- **数据库**：默认 SQLite（通过 `DATABASE_URL` 可切换至 Supabase/PostgreSQL）
- **前端**：Jinja2 + 原生 JS（含语音识别、行程渲染、费用管理、地图）
- **AI 能力**：可配置阿里云 DashScope / OpenAI / Mock
- **语音识别**：浏览器 Web Speech API；可选科大讯飞 IAT REST API

## 📦 目录结构

```
├─ app/                 # FastAPI 应用
│  ├─ api/              # REST API 路由
│  ├─ core/             # 配置、安全工具
│  ├─ db/               # 数据库会话 & 初始化
│  ├─ models/           # SQLAlchemy 模型
│  ├─ repositories/     # 数据访问封装
│  ├─ schemas/          # Pydantic 模型
│  ├─ services/         # LLM / Speech / Planning 服务
│  ├─ static/           # 前端静态资源（CSS、JS）
│  └─ templates/        # Jinja2 页面
├─ docs/                # 架构说明、PDF 等
├─ .github/workflows/   # GitHub Actions CI
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
├─ README.md
└─ .env.example
```

## 🚀 本地开发

1. **准备环境**

   ```bash
   python -m venv .venv
  .\.venv\Scripts\activate  # Windows PowerShell
   pip install -r requirements.txt
   cp .env.example .env
   ```

2. **启动服务**

   ```bash
   uvicorn app.main:app --reload
   ```

3. **访问页面**

   打开浏览器访问 [http://localhost:8000](http://localhost:8000)，使用界面完成注册、登录、语音输入并生成行程。

4. **API 文档**

   - FastAPI Docs: `http://localhost:8000/docs`
   - Redoc: `http://localhost:8000/redoc`

## 🔐 环境变量

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `ENVIRONMENT` | 运行环境（development/production） | development |
| `SECRET_KEY` | JWT 加密密钥 | change-me |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | 1440 |
| `DATABASE_URL` | 数据库地址（支持 sqlite / postgres / supabase） | sqlite+aiosqlite:///./travel_planner.db |
| `LLM_PROVIDER` | `mock` / `dashscope` / `openai` | mock |
| `LLM_MODEL` | LLM 模型名称 | qwen-turbo |
| `LLM_API_KEY` | LLM Key，提交作业需保证 3 个月内有效 | 空 |
| `LLM_ENDPOINT` | 自定义 LLM Endpoint | 空 |
| `SPEECH_PROVIDER` | `web` / `iflytek` | web |
| `IFLYTEK_APP_ID` | 科大讯飞 App ID | 空 |
| `IFLYTEK_API_KEY` | 科大讯飞 API Key | 空 |
| `AMAP_API_KEY` | 高德地图 JS API Key | 空 |

> **敏感信息安全提醒**：请勿将任何真实 API Key 提交到 Git 仓库。可通过设置页面（`/settings`）在浏览器本地保存 Key，再由前端在调用时传递给后端。

## 🗺️ 语音 & 地图配置

- **语音识别**：
  - 默认使用浏览器 Web Speech API（Chrome/Edge，需 HTTPS 或 localhost）。
  - 切换至科大讯飞：在 `.env` 或设置页面填写 `IFLYTEK_APP_ID` 与 `IFLYTEK_API_KEY`。
- **地图**：
  - 在 `.env` 或设置页面填写 `AMAP_API_KEY`，刷新后即可加载高德地图。

## 🧠 LLM 行程规划

1. **Mock 模式（默认）**：不依赖真实模型，使用规则生成示例行程，便于快速演示。
2. **阿里云 DashScope**：
   - 在 `.env` 设置 `LLM_PROVIDER=dashscope`，并提供 `LLM_API_KEY`。
   - 可自定义 `LLM_ENDPOINT`（默认官方地址）。
3. **OpenAI**：
   - 设置 `LLM_PROVIDER=openai`，填入 `LLM_API_KEY`（以及自定义 `LLM_ENDPOINT`，如 Azure）。

## 💰 费用记录

- 生成行程后可直接在「费用记录」中添加开销（类别、金额、备注）。
- 系统自动合计费用总额，为行程预算做对比。
- 后端持久化存储，登录账号可跨设备同步。

