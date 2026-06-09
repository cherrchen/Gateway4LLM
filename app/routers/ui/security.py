from fastapi import Request

from app.deps import SessionDep, get_current_user
from app.models import User


def user_or_none(request: Request, session: SessionDep) -> User | None:
    try:
        return get_current_user(session, access_token=request.cookies.get("access_token"))
    except Exception:
        return None
