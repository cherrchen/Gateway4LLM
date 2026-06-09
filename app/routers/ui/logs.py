from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from sqlmodel import desc, select

from app.deps import SessionDep, get_current_user
from app.models import GatewayLog
from app.routers.ui.templates import templates

router = APIRouter(prefix="/ui/logs")


@router.get("", response_class=HTMLResponse)
def list_logs(request: Request, session: SessionDep, provider: str | None = None) -> Response:
    user = get_current_user(session, access_token=request.cookies.get("access_token"))
    query = select(GatewayLog).where(GatewayLog.user_id == user.id)
    if provider:
        query = query.where(GatewayLog.provider == provider)
    logs = session.exec(query.order_by(desc(GatewayLog.created_at)).limit(50)).all()
    return templates.TemplateResponse(
        request,
        "partials/logs.html",
        {"logs": logs, "provider": provider or ""},
    )
