# Gateway4LLM

FastAPI 后端 LLM 网关，支持用户 JWT 登录、业务 Bearer API Key、OpenAI Chat Completions、OpenAI Responses、Anthropic Messages、关键操作日志和 HTMX 演示界面。

## 环境

- Python: 3.13
- 环境管理: `uv`
- 默认数据库: SQLite
- 可选数据库: PostgreSQL

## 启动

```powershell
uv sync --python 3.13
uv run uvicorn app.main:app --reload
```

访问 HTMX 演示界面：

```text
http://127.0.0.1:8000/
```

首次创建的用户会自动成为管理员。演示界面可以登录、创建/撤销业务 API Key、查看日志、发起 mock 网关请求。

## 配置

所有配置通过环境变量管理，前缀为 `G4L_`。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `G4L_DATABASE_URL` | `sqlite:///./gateway4llm.db` | SQLite 或 PostgreSQL URL |
| `G4L_JWT_SECRET` | `change-me-in-production` | JWT 签名密钥，生产必须替换 |
| `G4L_API_KEY_HASH_SECRET` | `change-me-api-key-pepper` | API Key HMAC 哈希 pepper，生产必须替换 |
| `G4L_DEFAULT_PROVIDER` | `mock` | 默认上游：`mock`、`openai`、`anthropic` |
| `G4L_DEFAULT_TARGET_INTERFACE` | `same` | 默认目标接口：`same`、`chat`、`responses`、`anthropic` |
| `G4L_OPENAI_API_KEY` | 空 | OpenAI 上游密钥 |
| `G4L_ANTHROPIC_API_KEY` | 空 | Anthropic 上游密钥 |
| `G4L_OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI 兼容上游地址 |
| `G4L_ANTHROPIC_BASE_URL` | `https://api.anthropic.com/v1` | Anthropic 上游地址 |

PostgreSQL 示例：

```powershell
$env:G4L_DATABASE_URL="postgresql://user:password@localhost:5432/gateway4llm"
uv run uvicorn app.main:app --reload
```

## 鉴权流程

管理系统使用 JWT Bearer：

```text
POST /api/auth/login
Authorization: Bearer <jwt>
```

实际接口：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/keys`
- `GET /api/keys`
- `POST /api/keys/{key_id}/revoke`
- `GET /api/logs`

业务系统使用用户签发的 Bearer API Key：

```text
Authorization: Bearer g4l_live_...
```

API Key 只在创建时返回一次，数据库只保存 HMAC-SHA256 哈希和短前缀。

## 网关接口

- `POST /v1/chat/completions`
- `POST /v1/responses`
- `POST /v1/messages`

可用请求头：

| Header | 说明 |
| --- | --- |
| `X-Gateway-Provider` | `mock`、`openai`、`anthropic` |
| `X-Gateway-Target-Interface` | `chat`、`responses`、`anthropic` |

默认 `mock` 上游会返回可预测响应，便于本地开发和测试。

## 格式转换

已实现并测试：

- Chat Completions -> Responses
- Responses -> Chat Completions
- Chat Completions -> Anthropic Messages
- Anthropic Messages -> Chat Completions
- Responses -> Anthropic Messages
- Anthropic Messages -> Responses

转换会尽量保留：

- messages、roles、system/developer prompt
- tools、tool_choice、tool calls、tool results
- response format / structured output
- temperature、top_p、max tokens、stop sequences、stream
- metadata、reasoning / thinking 字段
- 供应商特有扩展字段

无法直接映射的字段会写入 `metadata` 中的明确扩展字段，例如 `openai_chat_extra`、`openai_responses_extra`、`anthropic_extra`。

## Streaming 限制

当请求包含 `stream: true` 时：

- `mock` 上游返回简单 SSE。
- live OpenAI / Anthropic 上游按目标接口透传 SSE 字节流。
- 流式日志会记录请求开始和元信息，不保存完整流式响应体。
- 跨供应商流式事件格式不会二次转换为另一家供应商的事件协议。

## 日志与脱敏

`GatewayLog` 会记录用户、API Key 前缀、路由、provider、源/目标接口、状态码、耗时、请求元信息、响应元信息和错误信息。

日志脱敏规则会移除：

- 原始 API Key
- Authorization Header
- 上游供应商密钥
- token、password、secret 等敏感字段

## 路由目录

路由按文件树分层聚合，新增模块时优先在对应目录加入子路由，再由该目录的 `__init__.py` 挂载。

```text
app/routers/
  __init__.py              # 应用总路由
  api/
    __init__.py            # /api 聚合
    auth.py                # /api/auth
    keys.py                # /api/keys
    logs.py                # /api/logs
  gateway/
    __init__.py            # 业务网关聚合
    common.py              # 网关共享处理、日志、provider/接口选择
    chat.py                # /v1/chat/completions
    responses.py           # /v1/responses
    anthropic.py           # /v1/messages
  ui/
    __init__.py            # HTMX UI 聚合
    pages.py               # /
    auth.py                # /ui/login, /ui/register, /ui/logout
    keys.py                # /ui/keys
    logs.py                # /ui/logs
    gateway_test.py        # /ui/gateway-test
    templates.py           # Jinja2Templates 实例
```

## 验证

```powershell
uv run pytest
uv run ruff check .
uv run mypy app
uv run python -c "from fastapi.testclient import TestClient; from app.main import create_app; c=TestClient(create_app()); print(c.get('/health').json())"
```

## 参考文档

实现接口 schema 和转换时参考了当前官方文档：

- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat/create-chat-completion)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses/create)
- [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages)
- [Anthropic Streaming Messages](https://platform.claude.com/docs/en/build-with-claude/streaming)

## License

This project is under CC BY-NC 4.0.

Legal Code: https://creativecommons.org/licenses/by-nc/4.0/
