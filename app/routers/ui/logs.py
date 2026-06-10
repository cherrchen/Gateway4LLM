from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from sqlmodel import desc, select

from app.deps import SessionDep, get_current_user
from app.models import GatewayLog
from app.routers.ui.templates import templates

router = APIRouter(prefix="/ui/logs")


@router.get("", response_class=HTMLResponse)
def list_logs(
    request: Request,
    session: SessionDep,
    provider: str | None = None,
    search: str | None = None,
    status: str | None = None,
) -> Response:
    user = get_current_user(session, access_token=request.cookies.get("access_token"))
    query = select(GatewayLog).where(GatewayLog.user_id == user.id)
    if provider:
        query = query.where(GatewayLog.provider == provider)
    if status == "success":
        query = query.where(GatewayLog.status_code < 400)
    elif status == "error":
        query = query.where(GatewayLog.status_code >= 400)
    logs = session.exec(query.order_by(desc(GatewayLog.created_at)).limit(50)).all()
    if search:
        needle = search.lower()
        logs = [
            log
            for log in logs
            if needle in log.route.lower()
            or needle in (log.api_key_prefix or "").lower()
            or needle in (log.error or "").lower()
        ]
    return templates.TemplateResponse(
        request,
        "partials/logs.html",
        {"logs": logs, "provider": provider or "", "search": search or "", "status": status or ""},
    )
