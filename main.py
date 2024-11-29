import asyncio
from src import OpenAiRunnerClass, ChromaVectorStore, PDFtoText
from src import MetadataRAG
import json
import os
import re

class AdvanceQuestionGenerator:
    def __init__(self, openai_key = None) -> None:
        self.openai = OpenAiRunnerClass(openai_key)
        self.RAG = ChromaVectorStore()
        self.pdf = PDFtoText()

    # Generate Level_1
    async def generate_level_1(self, pdf_path: str) -> dict:
        """
        Asynchronously generate Level 1 questions from a PDF.

        Args:
            pdf_path (str): Path to the input PDF file.

        Returns:
            dict: Generated topics and questions.
        """
        # Extract all text from PDF in a separate thread
        all_text = await asyncio.to_thread(self.pdf.extract_all_text, pdf_path)
        
        # Generate topics and MCQs using OpenAI
        res = await self.openai.generate_topics_and_mcqs(context=all_text)

        return res

    async def _process_input_pdf(self, pdf_path: str) -> str:
        """
        Process the input PDF path to create a sanitized PDF name.

        Args:
            pdf_path (str): Path to the input PDF file.

        Returns:
            str: Sanitized PDF name.
        """
        # Extract the base name of the file regardless of path separators
        pdf_name = os.path.basename(pdf_path)
        
        # Replace spaces with underscores and remove other special characters
        # This regex keeps alphanumerics, underscores, and dots (for the extension)
        sanitized_pdf_name = re.sub(r'[^\w\.]', '_', pdf_name)
        
        return sanitized_pdf_name

    async def _process_documents_context(self, rag_output: list) -> str:
        """
        Process RAG output to create a consolidated context string.

        Args:
            rag_output (list): List of documents with metadata.

        Returns:
            str: Consolidated context string.
        """
        context = ""
        for document in rag_output:
            context_n = f"{document['document']} Page number: {document['metadata']['page_number']}\n"
            context += context_n
        return context

    async def generate_chat_RAG(self, question, pdf_path):
        collection_name = await self.ingest_input_pdf(pdf_path)

        # Noe Fetch relevant documents for this question from this collection

        results, output = await asyncio.to_thread(
            self.RAG.fetch_relevant_documents, question, collection_name, top_k=3
        ) 

        context = await self._process_documents_context(output)
        ans = await self.openai.chat(context=context, question=question)

        return ans, output



    

    async def ingest_input_pdf(self, pdf_path):
        all_text = await asyncio.to_thread(self.pdf.extract_all_text_page_wise, pdf_path)
        
        # Process PDF name
        collection_name = await self._process_input_pdf(pdf_path)
        
        # Store texts in RAG vector store in a separate thread
        await asyncio.to_thread(self.RAG.store_texts, all_text, collection_name=collection_name)

        return collection_name


    # Generate Level_2
    async def generate_level_2(self, pdf_path: str) -> dict:
        """
        Asynchronously generate Level 2 questions from a PDF using Retrieval-Augmented Generation (RAG).

        Args:
            pdf_path (str): Path to the input PDF file.

        Returns:
            dict: Metadata and generated questions.
        """
        # Extract all text and page-wise text from PDF in separate threads
        all_text_str = await asyncio.to_thread(self.pdf.extract_all_text, pdf_path)

        collection_name = await self.ingest_input_pdf(pdf_path)

        # Generate book information asynchronously
        book_info = await self.openai.generate_book_title(all_text_str)
        main_topics = book_info.get("main_topics", [])

        all_questions = []

        # Create a list of tasks for each topic to generate MCQs concurrently
        tasks = [
            self._process_topic(topic, all_text_str, collection_name)
            for topic in main_topics
        ]

        # Execute all tasks concurrently
        questions_list = await asyncio.gather(*tasks)

        # Aggregate all questions
        for questions in questions_list:
            all_questions.extend(questions)

        # Create metadata object
        obj = MetadataRAG(
            total_questions=len(all_questions), 
            book_title=book_info.get("book_title", ""),
            tool_used=self.openai.model_name,
            generation_method=self.RAG.method,
            embedding_model=self.RAG.embeddings_model_name, 
            vectore_store=self.RAG.vector_store
        )

        return {
            "metadata": obj.model_dump(),
            "questions": all_questions
        }

    async def _process_topic(self, topic: str, context_str: str, collection_name: str) -> list:
        """
        Asynchronously process a single topic to generate MCQs.

        Args:
            topic (str): The topic for which to generate questions.
            context_str (str): The context string extracted from the PDF.
            collection_name (str): Name of the RAG collection.

        Returns:
            list: List of generated questions for the topic.
        """
        print(f"Processing topic: {topic}")
        
        # Fetch relevant documents from RAG in a separate thread
        results, output = await asyncio.to_thread(
            self.RAG.fetch_relevant_documents, topic, collection_name, top_k=1
        )
        
        # Process the fetched documents to create context
        context = await self._process_documents_context(output)
        
        # Generate MCQs asynchronously using OpenAI
        questions = await self.openai.generate_mcqs(context=context, topic=topic, n=10)
        
        # Add source documents to each question
        for question in questions.get('questions', []):
            question['source'] = output
        
        return questions.get('questions', [])

# Example usage
async def main():
    gen = AdvanceQuestionGenerator()
    pdf_path = r"data/Project Management.pdf"
    
    # Generate Level 2 questions
    res = await gen.generate_level_1(pdf_path)
    
    # Save the results to a JSON file
    with open("level_2_auto_id.json", "w") as f:
        json.dump(res, f, indent=4)
    print("Level 2 questions generated and saved to level_2_auto_id.json")

if __name__ == "__main__":
    asyncio.run(main())
