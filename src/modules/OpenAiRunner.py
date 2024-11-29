import asyncio
from SimplerLLM.language.llm import LLM, LLMProvider
from SimplerLLM.language.llm_addons import generate_pydantic_json_model as gen_json
from src.constants import QuestionsModel, BookInfo, Metadata, ChatResponse
import json
from dotenv import load_dotenv
import os

load_dotenv()

class OpenAiRunnerClass:
    def __init__(self, model_name: str = "gpt-4o", openai_key  = None) -> None:
        self.model_name = model_name

        with open(r"src\constants\level_1_question_prompt.prompt", "r",encoding = "utf-8") as f:
            self.question_prompt = f.read()
        
        with open(r"src\constants\level_1_topics.prompt", "r",encoding = "utf-8") as f:
            self.topics_prompt = f.read()
        
        with open(r"src\constants\chat_prompt.prompt", "r",encoding = "utf-8") as f:
            self.chat_prompt = f.read()
        
        if not openai_key:
            self.openai_key = os.getenv("OPENAI_API_KEY")
        else:
            self.openai_key = openai_key
        self.llm_instance = LLM.create(provider=LLMProvider.OPENAI, model_name=model_name, api_key=self.openai_key)
    
    def _format_prompt_mcq(self, context: str, prompt: str, topic: str, n: int) -> str:
        return prompt.format(context=context, topic=topic, n=n)
    
    def _format_prompt(self, context: str, prompt: str) -> str:
        return prompt.format(context=context)
    
    def _format_prompt_chat(self, context, question, prompt):
            return prompt.format(context = context, question=question) 
    
    
    async def generate_mcqs(self, context: str, topic: str, n: int = 5) -> dict:
        """
        Asynchronously generate multiple-choice questions.
        """
        prompt = self._format_prompt_mcq(context, self.question_prompt, topic=topic, n=n)
        # Run the synchronous gen_json in a separate thread
        json_response = await asyncio.to_thread(
            gen_json, model_class=QuestionsModel, prompt=prompt, llm_instance=self.llm_instance
        )
        # Parse the JSON response
        questions = json.loads(json_response.to_json_schema())
        return questions
    async def chat(self, context, question):
        prompt = self._format_prompt_chat(context=context, question=question, prompt=self.chat_prompt)

        answer = gen_json(llm_instance=self.llm_instance, model_class=ChatResponse, prompt=prompt)

        return answer.model_dump()

    
    async def generate_mcq_with_RAG(self, context: str, topic: str, documents: list, n: int = 5) -> dict:
        """
        Asynchronously generate MCQs with Retrieval-Augmented Generation (RAG).
        """
        questions = await self.generate_mcqs(context=context, topic=topic, n=n)
        # Add source documents to each question
        for question in questions.get('questions', []):
            question['source'] = documents
        return questions
    
    async def generate_book_title(self, context: str) -> dict:
        """
        Asynchronously generate book title and main topics.
        """
        prompt = self._format_prompt(context, self.topics_prompt)
        # Run the synchronous gen_json in a separate thread
        json_response = await asyncio.to_thread(
            gen_json, model_class=BookInfo, prompt=prompt, llm_instance=self.llm_instance
        )

        obj = BookInfo(**(json_response.model_dump()))
        # Parse the JSON response
        return json.loads(obj.to_json_schema())
    
    async def generate_topics_and_mcqs(self, context: str) -> dict:
        """
        Asynchronously generate book topics and associated MCQs.
        """
        # Generate book information
        book_info = await self.generate_book_title(context)
        main_topics = book_info.get("main_topics", [])
        
        # Create tasks for generating MCQs for each topic
        tasks = [
            self.generate_mcqs(context, topic=topic)
            for topic in main_topics
        ]
        
        # Run all tasks concurrently
        questions_list = await asyncio.gather(*tasks)
        
        # Aggregate all questions
        all_questions = []
        for questions in questions_list:
            all_questions.extend(questions.get('questions', []))
        
        # Create metadata
        metadata = Metadata(
            tool_used=self.model_name,
            total_questions=len(all_questions),
            book_title=book_info.get("book_title", "")
        )
        
        return  {
                "metadata": metadata.model_dump(),
                "questions": all_questions
            }

# Example usage:
# async def main():
#     runner = OpenAiRunnerClass()
#     context = "Your context here"
#     result = await runner.generate_topics_and_mcqs(context)
#     print(json.dumps(result, indent=2))
#
# asyncio.run(main())
