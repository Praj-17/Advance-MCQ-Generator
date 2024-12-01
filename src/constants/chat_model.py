from pydantic import BaseModel, Field
from typing import List, Optional
import json
from datetime import datetime
import uuid

class ChatResponse(BaseModel):
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    question: Optional[str]
    answer: str
    documents: Optional[list[dict]]