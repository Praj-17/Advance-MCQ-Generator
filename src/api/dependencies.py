# app/dependencies.py
from fastapi import Header, HTTPException, Depends
from typing import Optional
from src  import AdvanceQuestionGeneratorClass

async def get_openai_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=400, detail="Missing  API Key in headers.")
    return x_api_key

async def get_question_generator(openai_key: str = Depends(get_openai_key)):
    generator = AdvanceQuestionGeneratorClass(openai_key=openai_key)
    return generator
