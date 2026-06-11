# Gateway4LLM

FastAPI 后端 LLM 网关，支持用户 JWT 登录、业务 Bearer API Key、OpenAI Chat Completions、OpenAI Responses、Anthropic Messages、Provider Registry、模型白名单、关键操作日志和 HTMX 管理界面。

## 环境

- Python: 3.13
- 环境管理: `uv`
- 默认数据库: SQLite
- 可选数据库: PostgreSQL

## 启动

```powershell
uv sync --python 3.13
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

访问 HTMX 演示界面：

```text
http://127.0.0.1:8000/
```

首次创建的用户会自动成为管理员。管理界面可以登录、创建/撤销业务 API Key、配置 Provider、配置可请求模型、测试 Provider 连通性、查看日志、发起 mock 网关请求。

## 配置

所有配置通过环境变量管理，前缀为 `G4L_`。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `G4L_DATABASE_URL` | `sqlite:///./gateway4llm.db` | SQLite 或 PostgreSQL URL |
| `G4L_JWT_SECRET` | `change-me-in-production` | JWT 签名密钥，生产必须替换 |
| `G4L_API_KEY_HASH_SECRET` | `change-me-api-key-pepper` | API Key HMAC 哈希 pepper，生产必须替换 |
| `G4L_DEFAULT_PROVIDER` | `mock` | 环境默认 provider，当请求、API Key 和管理面板默认值都未配置时使用 |
| `G4L_DEFAULT_MODEL` | `mock-model` | 环境默认模型，当请求、API Key、provider 和模型默认值都未配置时使用 |
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

## 数据库迁移

Schema 变更由 Alembic 管理，应用启动时会执行 `alembic upgrade head` 并 seed 内置 mock/openai/anthropic 配置。不要把临时补列逻辑放在启动路径里长期维护。

常用命令：

```powershell
uv run alembic revision --autogenerate -m "describe schema change"
uv run alembic upgrade head
```

当前 migration 会创建 `User`、`BusinessApiKey`、`GatewayLog`、`ProviderConfig`、`ModelConfig`、`ProviderModel`、`RoutingRule`，并包含 Business API Key 的 `default_provider`、`default_model`、`allowed_models` policy 字段。

## Provider Registry 架构

网关不再在路由或 `app/upstream.py` 中硬编码 provider 分支。请求链路现在是：

1. 读取入口接口：`chat`、`responses` 或 `anthropic`。
2. 按优先级解析 provider、模型和目标接口。
3. 校验 ProviderConfig、ModelConfig、API Key 策略、接口支持和 streaming 支持。
4. 将对外模型名映射为上游真实模型名，并合并模型默认参数。
5. 调用 `convert_request` 转换请求格式。
6. 从 `provider_registry` 获取 provider 类型并调用 `send` 或 `stream`。
7. 写入脱敏日志。

内置 provider 类型：

- `mock`：本地可预测响应，测试默认不依赖真实密钥。
- `openai`：OpenAI Chat Completions / Responses。
- `anthropic`：Anthropic Messages。

运行时注册 provider：

```python
from app.providers.mock import MockProvider
from app.providers.registry import provider_registry

provider_registry.register(MockProvider())
provider = provider_registry.get("mock")
all_providers = provider_registry.list()
```

新增 provider 类型的最小示例：

```python
from app.providers.base import GatewayProvider, ProviderResponse


class AcmeProvider(GatewayProvider):
    name = "acme"
    display_name = "Acme"
    supported_interfaces = {"chat"}
    supports_streaming = False

    async def send(self, interface, body, config, model):
        self.validate_config(config)
        return ProviderResponse(status_code=200, body={"ok": True})

    def stream(self, interface, body, config, model):
        raise NotImplementedError
```

然后在启动时注册：

```python
provider_registry.register(AcmeProvider())
```

## Provider 和模型配置

管理面板包含四个 provider/routing 区域：

- Provider 管理：查看、创建、编辑、启用/禁用 provider，设置显示名称、类型、base URL、密钥环境变量引用、默认目标接口、默认模型、streaming、超时、系统默认，并测试连通性。
- ProviderModel 目录：查看、创建、编辑、启用/禁用上游模型目录，维护能力标签、价格、健康状态、默认目标接口和 GatewayModel 映射状态。
- GatewayModel 管理：查看、创建、编辑、启用/禁用模型映射，设置 provider、对外模型名、上游真实模型名、支持接口、默认目标接口、默认参数、streaming、备注和默认模型。
- Routing Rules：查看、创建、编辑、启用/禁用 GatewayModel 到 ProviderModel 的 fixed、fallback、weighted、custom 路由规则。fixed/fallback/weighted 会参与网关运行时解析。

REST 管理接口：

- `GET /api/provider-types`
- `GET /api/providers`
- `GET /api/providers/{provider_id}`
- `POST /api/providers`
- `PATCH /api/providers/{provider_id}`
- `POST /api/providers/{provider_id}/enable`
- `POST /api/providers/{provider_id}/disable`
- `POST /api/providers/{provider_id}/set-default`
- `DELETE /api/providers/{provider_id}`
- `POST /api/providers/{provider_id}/test`
- `GET /api/models`
- `GET /api/models/{model_id}`
- `POST /api/models`
- `PATCH /api/models/{model_id}`
- `POST /api/models/{model_id}/enable`
- `POST /api/models/{model_id}/disable`
- `POST /api/models/{model_id}/set-default`
- `DELETE /api/models/{model_id}`
- `GET /api/provider-models`
- `GET /api/provider-models/{provider_model_id}`
- `POST /api/provider-models`
- `PATCH /api/provider-models/{provider_model_id}`
- `POST /api/provider-models/{provider_model_id}/enable`
- `POST /api/provider-models/{provider_model_id}/disable`
- `POST /api/provider-models/{provider_model_id}/set-default`
- `POST /api/provider-models/{provider_model_id}/test`
- `POST /api/providers/{provider_id}/provider-models/sync`
- `DELETE /api/provider-models/{provider_model_id}`
- `GET /api/routing-rules`
- `GET /api/routing-rules/{rule_id}`
- `POST /api/routing-rules`
- `PATCH /api/routing-rules/{rule_id}`
- `POST /api/routing-rules/{rule_id}/enable`
- `POST /api/routing-rules/{rule_id}/disable`
- `DELETE /api/routing-rules/{rule_id}`
- `GET /api/settings/routing`
- `PATCH /api/settings/routing`

`DELETE /api/providers/{provider_id}`、`DELETE /api/models/{model_id}`、`DELETE /api/provider-models/{provider_model_id}` 和 `DELETE /api/routing-rules/{rule_id}` 会返回明确错误：当前设计不支持硬删除，只支持禁用，以保留模型、策略和历史日志关联。

新增模型配置示例：

```json
{
  "provider_config_id": 1,
  "public_model_name": "gpt-4.1-mini",
  "upstream_model_name": "gpt-4.1-mini",
  "supported_interfaces": ["chat", "responses"],
  "supports_streaming": true,
  "default_target_interface": "same",
  "default_parameters": {"temperature": 0.2},
  "is_enabled": true
}
```

Provider 选择优先级：

1. 请求头 `X-Gateway-Provider`
2. 请求体 `gateway.provider`
3. API Key 绑定的默认 provider
4. 管理面板中标记为系统默认的 ProviderConfig
5. 环境变量 `G4L_DEFAULT_PROVIDER`

目标接口选择优先级：

1. 请求头 `X-Gateway-Target-Interface`
2. 请求体 `gateway.target_interface`
3. 模型配置的默认目标接口
4. Provider 配置的默认目标接口
5. 环境变量 `G4L_DEFAULT_TARGET_INTERFACE`

如果目标接口是 `same`，会使用当前入口接口。

模型选择和映射规则：

1. 优先使用请求体原始 `model`。
2. 如果请求体没有 `model`，使用 API Key 默认模型。
3. 其次使用 Provider 配置默认模型。
4. 其次使用该 Provider 下标记为默认的 ModelConfig。
5. 最后使用 `G4L_DEFAULT_MODEL`。

请求中的对外模型名必须存在于当前 Provider 的 ModelConfig 且处于启用状态。转发前会把 `public_model_name` 替换为 `upstream_model_name`，并合并 `default_parameters`。

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
- `PATCH /api/keys/{key_id}`
- `POST /api/keys/{key_id}/revoke`
- `GET /api/logs`
- `GET /api/provider-types`
- `GET /api/providers`
- `GET /api/providers/{provider_id}`
- `POST /api/providers`
- `PATCH /api/providers/{provider_id}`
- `POST /api/providers/{provider_id}/enable`
- `POST /api/providers/{provider_id}/disable`
- `POST /api/providers/{provider_id}/set-default`
- `POST /api/providers/{provider_id}/test`
- `GET /api/models`
- `GET /api/models/{model_id}`
- `POST /api/models`
- `PATCH /api/models/{model_id}`
- `POST /api/models/{model_id}/enable`
- `POST /api/models/{model_id}/disable`
- `POST /api/models/{model_id}/set-default`
- `GET /api/provider-models`
- `GET /api/provider-models/{provider_model_id}`
- `POST /api/provider-models`
- `PATCH /api/provider-models/{provider_model_id}`
- `POST /api/provider-models/{provider_model_id}/enable`
- `POST /api/provider-models/{provider_model_id}/disable`
- `POST /api/provider-models/{provider_model_id}/set-default`
- `POST /api/provider-models/{provider_model_id}/test`
- `POST /api/providers/{provider_id}/provider-models/sync`
- `GET /api/routing-rules`
- `GET /api/routing-rules/{rule_id}`
- `POST /api/routing-rules`
- `PATCH /api/routing-rules/{rule_id}`
- `POST /api/routing-rules/{rule_id}/enable`
- `POST /api/routing-rules/{rule_id}/disable`
- `GET /api/settings/routing`
- `PATCH /api/settings/routing`

业务系统使用用户签发的 Bearer API Key：

```text
Authorization: Bearer g4l_live_...
```

API Key 只在创建时返回一次，数据库只保存 HMAC-SHA256 哈希和短前缀。

API Key policy 可通过创建或 `PATCH /api/keys/{key_id}` 设置：

- `default_provider`
- `default_model`
- `allowed_models`

`allowed_models` 对外以数组呈现；数据库当前可继续存 JSON 字符串，但读写都由 service 层封装。已 revoke 的 API Key 不能更新策略，也不能继续调用网关。

## 网关接口

- `POST /v1/chat/completions`
- `POST /v1/responses`
- `POST /v1/messages`

可用请求头：

| Header | 说明 |
| --- | --- |
| `X-Gateway-Provider` | ProviderConfig 的 `name`，例如 `mock`、`openai`、`anthropic` |
| `X-Gateway-Target-Interface` | `same`、`chat`、`responses`、`anthropic` |

默认启动会创建内置 `mock` ProviderConfig 和 `mock-model` ModelConfig。`mock` 上游会返回可预测响应，便于本地开发和测试。

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
- 如果 provider 类型、ProviderConfig 或 ModelConfig 禁用了 streaming，请求会返回清晰的 400 错误。

## 密钥管理

ProviderConfig 支持使用环境变量引用配置上游密钥，例如：

```text
env:OPENAI_API_KEY
G4L_OPENAI_API_KEY
```

API 响应和 HTMX 管理页面不会显示 `api_key_secret_ref` 的完整值，日志也不会记录 Authorization、上游 provider key、token、secret 或敏感 header。生产环境建议接入 KMS、Vault 或云厂商 Secret Manager，只在数据库保存密钥引用，不保存真实明文密钥。

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
    providers.py           # /api/providers, /api/models, /api/provider-models, /api/routing-rules
  gateway/
    __init__.py            # 业务网关聚合
    common.py              # 网关共享处理、解析配置、调用 provider、日志
    chat.py                # /v1/chat/completions
    responses.py           # /v1/responses
    anthropic.py           # /v1/messages
  ui/
    __init__.py            # HTMX UI 聚合
    pages.py               # /
    auth.py                # /ui/login, /ui/register, /ui/logout
    keys.py                # /ui/keys
    logs.py                # /ui/logs
    providers.py           # /ui/providers, /ui/models, /ui/provider-models, /ui/routing-rules
    gateway_test.py        # /ui/gateway-test
    templates.py           # Jinja2Templates 实例
app/providers/
  base.py                  # Provider 抽象和 ProviderResponse
  registry.py              # ProviderRegistry
  mock.py                  # mock provider
  openai.py                # OpenAI provider
  anthropic.py             # Anthropic provider
app/services/
  provider_configs.py      # ProviderConfig/ModelConfig service 和网关解析规则
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
