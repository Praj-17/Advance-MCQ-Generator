# app/main.py

import asyncio
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
from src import get_question_generator
from src import (
    IngestPDFResponse,
    GenerateLevel1Response,
    GenerateLevel2Response,
    ChatResponse,
    ResetDataResponse
)
from src import AdvanceQuestionGeneratorClass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Advanced Question Generator API",
    description="API for generating Level 1 & 2 questions and performing chat operations using Gemini and RAG.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)
# Wrapper class to map 'filename' to 'name' and provide a synchronous 'read' method
class UploadFileWrapper:
    def __init__(self, upload_file: UploadFile):
        self.filename = upload_file.filename
        self.name = upload_file.filename  # Map 'filename' to 'name'
        self.file = upload_file.file
        self.content_type = upload_file.content_type

    def read(self):
        """
        Synchronously read the entire content of the uploaded file.
        """
        try:
            # Move the cursor to the beginning of the file to ensure full read
            self.file.seek(0)
            return self.file.read()
        except Exception as e:
            logger.error(f"Error reading file content: {e}")
            raise

@app.post("/ingest_pdf", response_model=IngestPDFResponse)
async def ingest_pdf(
    pdf_file: UploadFile = File(...),
    generator: AdvanceQuestionGeneratorClass = Depends(get_question_generator)
):
    """
    Ingests a PDF file, processes it, and stores embeddings.
    """
    if not pdf_file.filename.lower().endswith('.pdf'):
        logger.error(f"Unsupported file type: {pdf_file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        logger.info(f"Received PDF file: {pdf_file.filename}")
        
        # Wrap the UploadFile to include 'name' attribute
        wrapped_pdf = UploadFileWrapper(pdf_file)
        
        collection_name = await generator.ingest_input_pdf(wrapped_pdf)
        logger.info(f"PDF ingested successfully. Collection name: {collection_name}")
        return IngestPDFResponse(collection_name=collection_name, status="success")
    except ValueError as ve:
        logger.error(f"ValueError during PDF ingestion: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception(f"Unexpected error during PDF ingestion: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while ingesting the PDF.")

@app.post("/generate_level_1", response_model=GenerateLevel1Response)
async def generate_level_1(
    collection_name: str = Form(...),
    generator: AdvanceQuestionGeneratorClass = Depends(get_question_generator)
):
    """
    Generates Level 1 questions from the ingested collection.
    """
    if not collection_name:
        logger.error("Collection name is required for generating Level 1 questions.")
        raise HTTPException(status_code=400, detail="Collection name is required.")
    
    try:
        logger.info(f"Generating Level 1 questions for collection: {collection_name}")
        result = await generator.generate_level_1(collection_name)
        print()
        logger.info(f"Level 1 questions generated successfully for collection: {collection_name}")
        return GenerateLevel1Response(**result)
    except ValueError as ve:
        logger.error(f"ValueError during Level 1 question generation: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception(f"Unexpected error during Level 1 question generation: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating Level 1 questions.")

@app.post("/generate_level_2", response_model=GenerateLevel2Response)
async def generate_level_2(
    collection_name: str = Form(...),
    generator: AdvanceQuestionGeneratorClass = Depends(get_question_generator)
):
    """
    Generates Level 2 questions using Retrieval-Augmented Generation (RAG).
    """
    if not collection_name:
        logger.error("Collection name is required for generating Level 2 questions.")
        raise HTTPException(status_code=400, detail="Collection name is required.")
    
    try:
        logger.info(f"Generating Level 2 questions for collection: {collection_name}")
        result = await generator.generate_level_2(collection_name)
        logger.info(f"Level 2 questions generated successfully for collection: {collection_name}")
        return GenerateLevel2Response(**result)
    except ValueError as ve:
        logger.error(f"ValueError during Level 2 question generation: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception(f"Unexpected error during Level 2 question generation: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating Level 2 questions.")

@app.post("/chat", response_model=ChatResponse)
async def chat(
    collection_name: str = Form(...),
    question: str = Form(...),
    generator: AdvanceQuestionGeneratorClass = Depends(get_question_generator)
):
    """
    Generates an answer to a user's question using RAG.
    """
    if not collection_name:
        logger.error("Collection name is required for chat.")
        raise HTTPException(status_code=400, detail="Collection name is required.")
    if not question.strip():
        logger.error("Question cannot be empty.")
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    try:
        logger.info(f"Generating chat response for question: '{question}' in collection: {collection_name}")
        answer, documents = await generator.generate_chat_RAG(question, collection_name)
        answer['documents'] = documents

        logger.info(f"Chat response generated successfully for question: '{question}'")
        return ChatResponse(**answer)
    except ValueError as ve:
        logger.error(f"ValueError during chat generation: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception(f"Unexpected error during chat generation: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the chat response.")

@app.post("/reset_data", response_model=ResetDataResponse)
async def reset_data(
    generator: AdvanceQuestionGeneratorClass = Depends(get_question_generator)
):
    """
    Resets the ingested data and clears the vector store.
    """
    try:
        logger.info("Resetting all ingested data and clearing the vector store.")
        await generator.reset_data()
        logger.info("Data reset successfully.")
        return ResetDataResponse(status="Data reset successfully")
    except Exception as e:
        logger.exception(f"Unexpected error during data reset: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while resetting the data.")
