from fastapi import APIRouter, Depends

from app.api.deps import get_chat_service, get_current_user
from app.db.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ChatSourceRead
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def ask(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    answer = await chat_service.ask(user_id=user.id, question=payload.question)
    return ChatResponse(
        answer=answer.answer,
        sources=[ChatSourceRead(**vars(s)) for s in answer.sources],
        confidence=answer.confidence,
        grounded=answer.grounded,
    )
