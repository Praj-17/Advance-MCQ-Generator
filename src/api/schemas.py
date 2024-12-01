# app/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class IngestPDFResponse(BaseModel):
    collection_name: str
    status: str

class GenerateLevel1Response(BaseModel):
    metadata: dict
    questions: List[dict]

class GenerateLevel2Response(BaseModel):
    metadata: dict
    questions: List[dict]

class ChatResponse(BaseModel):
    generated_at: str
    question: str
    answer: str
    documents: List[dict]

class ResetDataResponse(BaseModel):
    status: str
