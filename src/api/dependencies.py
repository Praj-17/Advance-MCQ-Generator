# app/dependencies.py
from fastapi import Header, HTTPException, Depends
from typing import Optional
from src  import AdvanceQuestionGeneratorClass

async def get_openai_key(x_openai_key: Optional[str] = Header(None)):
    if not x_openai_key:
        raise HTTPException(status_code=400, detail="Missing OpenAI API Key in headers.")
    return x_openai_key

async def get_question_generator(openai_key: str = Depends(get_openai_key)):
    generator = AdvanceQuestionGeneratorClass(openai_key=openai_key)
    return generator
