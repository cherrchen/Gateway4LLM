from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.deps import SessionDep
from app.routers.ui.security import user_or_none
from app.routers.ui.templates import templates

router = APIRouter()

PAGE_META = {
    "dashboard": ("Dashboard", "系统状态、Provider 健康和网关测试入口"),
    "providers": ("Providers", "外部模型服务商配置与连接测试"),
    "provider-models": ("Provider Models", "Internal model from provider"),
    "gateway-models": ("Gateway Models", "Public model name used by clients"),
    "routing": ("Routing Rules", "GatewayModel 到 ProviderModel 的路由策略"),
    "api-keys": ("API Keys", "业务系统调用 Gateway 的凭证"),
    "logs": ("Logs", "请求、错误和路由决策日志"),
    "settings": ("Settings", "基础配置、UI 偏好和安全预留项"),
}


@router.get("/", response_class=HTMLResponse)
def index(request: Request, session: SessionDep, page: str = "dashboard") -> Response:
    user = user_or_none(request, session)
    if not user:
        return templates.TemplateResponse(request, "login.html")
    active_page = page if page in PAGE_META else "dashboard"
    title, subtitle = PAGE_META[active_page]
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "active_page": active_page,
            "page_title": title,
            "page_subtitle": subtitle,
        },
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, session: SessionDep) -> Response:
    user = user_or_none(request, session)
    if user:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "login.html")


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, session: SessionDep) -> Response:
    user = user_or_none(request, session)
    if user:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "login.html")
