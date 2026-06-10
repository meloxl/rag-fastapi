from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="用户问题")


class SourceItem(BaseModel):
    category: str
    source: str
    preview: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceItem]


class BuildKbResponse(BaseModel):
    status: str
    message: str
    chunk_count: int


class UploadResponse(BaseModel):
    status: str
    message: str
    filename: str


class HealthResponse(BaseModel):
    status: str
    kb_built: bool
    docs_count: int
    embed_provider: str
    embed_model: str
    llm_model: str
