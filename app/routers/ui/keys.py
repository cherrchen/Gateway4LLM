from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, Response

from app.deps import SessionDep, get_current_user
from app.routers.ui.templates import templates
from app.schemas import ApiKeyCreate
from app.services.api_keys import create_user_api_key, list_user_api_keys, revoke_user_api_key

router = APIRouter(prefix="/ui/keys")


@router.get("", response_class=HTMLResponse)
def list_keys(request: Request, session: SessionDep) -> Response:
    user = get_current_user(session, access_token=request.cookies.get("access_token"))
    keys = list_user_api_keys(session, user)
    return templates.TemplateResponse(request, "partials/keys.html", {"keys": keys})


@router.post("", response_class=HTMLResponse)
def create_key(request: Request, session: SessionDep, name: str = Form()) -> Response:
    user = get_current_user(session, access_token=request.cookies.get("access_token"))
    created = create_user_api_key(session, user, ApiKeyCreate(name=name))
    keys = list_user_api_keys(session, user)
    return templates.TemplateResponse(
        request,
        "partials/keys.html",
        {"keys": keys, "created_key": created.api_key},
    )


@router.post("/{key_id}/revoke", response_class=HTMLResponse)
def revoke_key(request: Request, key_id: int, session: SessionDep) -> Response:
    user = get_current_user(session, access_token=request.cookies.get("access_token"))
    revoke_user_api_key(session, user, key_id)
    keys = list_user_api_keys(session, user)
    return templates.TemplateResponse(request, "partials/keys.html", {"keys": keys})
