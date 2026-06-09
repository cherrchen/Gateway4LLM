from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from app.deps import SessionDep
from app.routers.ui.security import user_or_none
from app.routers.ui.templates import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request, session: SessionDep) -> Response:
    user = user_or_none(request, session)
    if not user:
        return templates.TemplateResponse(request, "login.html")
    return templates.TemplateResponse(request, "dashboard.html", {"user": user})
