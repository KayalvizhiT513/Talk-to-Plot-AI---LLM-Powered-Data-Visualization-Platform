from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt for data generation")


class PlotData(BaseModel):
    name: str
    data: List[Dict[str, Any]]


class ChatResponse(BaseModel):
    plot_name: str
    processed_data: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
