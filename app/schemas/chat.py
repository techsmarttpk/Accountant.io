from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2_000)


class ChatSourceRead(BaseModel):
    source: str
    title: str
    score: float
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSourceRead]
    confidence: float
    grounded: bool
