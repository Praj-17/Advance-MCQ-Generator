# app/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class IngestPDFResponse(BaseModel):
    collection_name: str
    status: str

class GenerateLevel1Response(BaseModel):
    topics: List[str]
    questions: List[str]

class GenerateLevel2Response(BaseModel):
    metadata: dict
    questions: List[dict]

class ChatResponse(BaseModel):
    answer: str
    documents: List[dict]

class ResetDataResponse(BaseModel):
    status: str
