from pydantic import BaseModel, Field
from typing import List, Optional
import json
from datetime import datetime
import uuid

class QuestionRAG(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    type: str
    question: str
    options: List[str]
    correct_answer: str
    page_number: int
    explanation: str

class QuestionsModelRAG(BaseModel):
    questions: List[QuestionRAG]

    def to_json_schema(self) -> str:
        """Convert the QuestionsModel instance to JSON with the required schema."""
        return json.dumps({
            "questions": [
                {
                    "id": question.id,
                    "topic": question.topic,
                    "type": question.type,
                    "question": question.question,
                    "options": question.options,
                    "correct_answer": question.correct_answer,
                    "page_number": question.page_number,
                    "explanation" : question.explanation
                }
                for question in self.questions
            ]
        }, indent=4)