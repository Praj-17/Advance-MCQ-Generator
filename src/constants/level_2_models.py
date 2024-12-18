from pydantic import BaseModel, Field
from datetime import datetime

class MetadataRAG(BaseModel):
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    total_questions: int
    book_title: str
    tool_used: str
    generation_method: str
    embedding_model: str
    vectore_store: str