from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from sqlmodel import func, select

from app.deps import SessionDep, get_current_user
from app.models import BusinessApiKey, GatewayLog, ModelConfig, ProviderConfig
from app.routers.ui.templates import templates

router = APIRouter(prefix="/ui")


@router.get("/dashboard-stats", response_class=HTMLResponse)
def dashboard_stats(request: Request, session: SessionDep) -> Response:
    get_current_user(session, access_token=request.cookies.get("access_token"))
    provider_count = session.exec(select(func.count()).select_from(ProviderConfig)).one()
    enabled_provider_count = session.exec(
        select(func.count()).select_from(ProviderConfig).where(ProviderConfig.is_enabled)
    ).one()
    model_count = session.exec(select(func.count()).select_from(ModelConfig)).one()
    key_count = session.exec(select(func.count()).select_from(BusinessApiKey)).one()
    request_count = session.exec(select(func.count()).select_from(GatewayLog)).one()
    error_count = session.exec(
        select(func.count()).select_from(GatewayLog).where(GatewayLog.status_code >= 400)
    ).one()
    avg_latency = session.exec(select(func.avg(GatewayLog.duration_ms))).one()
    error_rate = (error_count / request_count * 100) if request_count else 0
    return templates.TemplateResponse(
        request,
        "partials/dashboard_stats.html",
        {
            "provider_count": provider_count,
            "enabled_provider_count": enabled_provider_count,
            "model_count": model_count,
            "key_count": key_count,
            "request_count": request_count,
            "error_rate": error_rate,
            "avg_latency": int(avg_latency or 0),
        },
    )


@router.get("/provider-health", response_class=HTMLResponse)
def provider_health(request: Request, session: SessionDep) -> Response:
    get_current_user(session, access_token=request.cookies.get("access_token"))
    providers = session.exec(select(ProviderConfig).order_by(ProviderConfig.name)).all()
    return templates.TemplateResponse(
        request,
        "partials/provider_health.html",
        {"providers": providers},
    )
