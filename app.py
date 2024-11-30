# app/main.py
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from src import get_question_generator
from src import (
    IngestPDFResponse,
    GenerateLevel1Response,
    GenerateLevel2Response,
    ChatResponse,
    ResetDataResponse
)
from src import AdvanceQuestionGeneratorClass

app = FastAPI(
    title="Advanced Question Generator API",
    description="API for generating Level 1 & 2 questions and performing chat operations using OpenAI and RAG.",
    version="1.0.0"
)

@app.post("/ingest_pdf", response_model=IngestPDFResponse)
async def ingest_pdf(
    pdf_file: UploadFile = File(...),
    generator:AdvanceQuestionGeneratorClass = Depends(get_question_generator)
):
    """
    Ingests a PDF file, processes it, and stores embeddings.
    """
    try:
        collection_name = await generator.ingest_input_pdf(pdf_file)
        return IngestPDFResponse(collection_name=collection_name, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_level_1", response_model=GenerateLevel1Response)
async def generate_level_1(
    collection_name: str,
    generator: AdvanceQuestionGeneratorClass = Depends(get_question_generator)
):
    """
    Generates Level 1 questions from the ingested collection.
    """
    try:
        result = await generator.generate_level_1(collection_name)
        return GenerateLevel1Response(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_level_2", response_model=GenerateLevel2Response)
async def generate_level_2(
    collection_name: str,
    generator: AdvanceQuestionGeneratorClass = Depends(get_question_generator)
):
    """
    Generates Level 2 questions using Retrieval-Augmented Generation (RAG).
    """
    try:
        result = await generator.generate_level_2(collection_name)
        return GenerateLevel2Response(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(
    collection_name: str,
    question: str,
    generator:AdvanceQuestionGeneratorClass = Depends(get_question_generator)
):
    """
    Generates an answer to a user's question using RAG.
    """
    try:
        answer, documents = await generator.generate_chat_RAG(question, collection_name)
        return ChatResponse(answer=answer, documents=documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset_data", response_model=ResetDataResponse)
async def reset_data(
    generator :AdvanceQuestionGeneratorClass= Depends(get_question_generator)
):
    """
    Resets the ingested data and clears the vector store.
    """
    try:
        await generator.reset_data()
        return ResetDataResponse(status="Data reset successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
