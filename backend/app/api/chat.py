"""Chat and Conversational Interaction Endpoints."""
from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatMessageSchema, ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest) -> ChatResponse:
    """Sends a chat message to the active AI provider (mock by default)."""
    try:
        return await chat_service.process_chat(request)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(exc)}",
        )


@router.get("/{conversation_id}", response_model=List[ChatMessageSchema])
async def get_conversation_history(conversation_id: str) -> List[ChatMessageSchema]:
    """Retrieves conversation turn history for a given conversation ID."""
    history = chat_service.get_conversation_history(conversation_id)
    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation '{conversation_id}' not found.",
        )
    return history
