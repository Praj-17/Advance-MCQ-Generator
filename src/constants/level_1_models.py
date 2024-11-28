from pydantic import BaseModel, Field
from typing import List, Optional
import json
from datetime import datetime
import uuid

class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    type: str
    question: str
    options: List[str]
    correct_answer: str
    page_number: int
    explanation: str

class QuestionsModel(BaseModel):
    questions: List[Question]

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

class BookInfo(BaseModel):
    book_title: str
    total_topics: int
    extraction_timestamp: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())
    main_topics: List[str]

    def to_json_schema(self) -> str:
        """Convert the BookInfo instance to JSON with the required schema."""
        return json.dumps({
            "book_title": self.book_title,
            "total_topics": self.total_topics,
            "extraction_timestamp": self.extraction_timestamp,
            "main_topics": self.main_topics
        }, indent=4)
    
class Metadata(BaseModel):
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    total_questions: int
    book_title: str
    tool_used: str



class ProjectManagementProfessionalGuide(BaseModel):
    book_info: BookInfo
    questions_data: QuestionsModel

    def to_json_schema(self) -> str:
        """Convert the entire ProjectManagementProfessionalGuide instance to JSON."""
        return json.dumps({
            "book_info": json.loads(self.book_info.to_json_schema()),
            "questions_data": json.loads(self.questions_data.to_json_schema())
        }, indent=4)

# Example Usage
if __name__ == "__main__":
    book_info = BookInfo(
        book_title="Project Management Professional Guide",
        total_topics=10,
        extraction_timestamp=datetime.now().isoformat(),
        main_topics=["Initiation", "Planning", "Execution", "Monitoring", "Closing"]
    )

    questions = [
        Question(
            topic="Initiation",
            type="Multiple Choice",
            question="What is the first phase of project management?",
            options=["Initiation", "Planning", "Execution", "Closure"],
            correct_answer="Initiation",
            page_number=10
        ),
        Question(
            topic="Planning",
            type="True/False",
            question="The planning phase involves defining the project scope.",
            options=["True", "False"],
            correct_answer="True",
            page_number=25
        ),
        # Add more questions as needed
    ]

    metadata = Metadata(
        total_questions=len(questions),
        book_title=book_info.book_title,
        tool_used="Custom Pydantic Model"
    )

    questions_model = QuestionsModel(
        metadata=metadata,
        questions=questions
    )

    guide = ProjectManagementProfessionalGuide(
        book_info=book_info,
        questions_data=questions_model
    )

    print(guide.to_json_schema())
