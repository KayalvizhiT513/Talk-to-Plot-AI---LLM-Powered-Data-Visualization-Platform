from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.data_processor import process_data
from app.services.openai_service import generate_data


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest) -> ChatResponse:
    try:
        raw_data = await generate_data(request.prompt)
        processed_data, plot_name = process_data(raw_data)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - passthrough for FastAPI error handling
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(plot_name=plot_name, processed_data=processed_data)
