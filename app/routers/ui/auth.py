from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlmodel import select

from app.deps import SessionDep
from app.models import User
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/ui")


@router.post("/register")
def register(session: SessionDep, email: str = Form(), password: str = Form()) -> Response:
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        has_users = session.exec(select(User)).first() is not None
        user = User(email=email, hashed_password=hash_password(password), is_admin=not has_users)
        session.add(user)
        session.commit()
        session.refresh(user)
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        "access_token",
        create_access_token(str(user.id)),
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/login")
def login(session: SessionDep, email: str = Form(), password: str = Form()) -> Response:
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.hashed_password):
        return HTMLResponse('<div class="alert error">登录失败</div>', status_code=401)
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        "access_token",
        create_access_token(str(user.id)),
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/logout")
def logout() -> Response:
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("access_token")
    return response
