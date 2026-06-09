import json

from fastapi import APIRouter
from sqlmodel import desc, select

from app.deps import CurrentUserDep, SessionDep
from app.models import GatewayLog
from app.schemas import GatewayLogRead

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=list[GatewayLogRead])
def list_logs(
    user: CurrentUserDep,
    session: SessionDep,
    provider: str | None = None,
    limit: int = 50,
) -> list[GatewayLogRead]:
    query = select(GatewayLog).where(GatewayLog.user_id == user.id)
    if provider:
        query = query.where(GatewayLog.provider == provider)
    rows = session.exec(query.order_by(desc(GatewayLog.created_at)).limit(min(limit, 200))).all()
    return [
        GatewayLogRead(
            **row.model_dump(exclude={"request_meta", "response_meta"}),
            request_meta=json.loads(row.request_meta or "{}"),
            response_meta=json.loads(row.response_meta or "{}"),
        )
        for row in rows
    ]
