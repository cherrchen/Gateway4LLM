from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.models.api_keys import APIKey
from app.schemas.chat_completion import ChatCompletionRequest, ChatCompletionResponse
from app.services.llm_service.llm_service import LLMService
from app.api.deps import get_llm_service
from app.deps import get_current_api_key

router = APIRouter()

@router.post("/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
        request: ChatCompletionRequest,
        llm_service: Annotated[LLMService, Depends(get_llm_service)],
        current_api_key: Annotated[APIKey, Depends(get_current_api_key)],
):
    try: 
        response = await llm_service.handle_chat_completion(request)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gateway Internal Error: {str(e)}")
