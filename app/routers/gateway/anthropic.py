from fastapi import APIRouter, Header, Request, Response

from app.deps import ApiKeyPrincipalDep, SessionDep
from app.routers.gateway.common import handle_gateway_request

router = APIRouter(tags=["gateway"])


@router.post("/v1/messages")
async def anthropic_messages(
    request: Request,
    session: SessionDep,
    principal: ApiKeyPrincipalDep,
    x_gateway_provider: str | None = Header(default=None),
    x_gateway_target_interface: str | None = Header(default=None),
) -> Response:
    return await handle_gateway_request(
        request, session, principal, "anthropic", x_gateway_provider, x_gateway_target_interface
    )
