import asyncio
from io import BytesIO
from .OpenAiRunner import OpenAiRunnerClass
from .RAG_implementation import ChromaVectorStore
from .pdf_to_text import PDFtoText
from src.constants import MetadataRAG
import re

class AdvanceQuestionGeneratorClass:
    def __init__(self, openai_key=None, model_name=None, temperature=0.7) -> None:
        self.openai = OpenAiRunnerClass(
            model_name=model_name,
            openai_key=openai_key,
            temperature=temperature
        )
        self.RAG = ChromaVectorStore(
            openai_api_key= openai_key)
        self.pdf = PDFtoText()
        self.ingested_pdfs = []  # List to keep track of ingested PDFs
        self.collection_texts = {}  # Dict to map collection_name to extracted text

    async def ingest_input_pdf(self, pdf_file):
        """
        Ingests the input PDF file and processes it to extract text and store embeddings.

        Args:
            pdf_file: The uploaded PDF file object.

        Returns:
            str: Name of the collection created for the PDF.
        """
        # Process PDF name
        collection_name = await self._process_input_pdf(pdf_file.name)

        if pdf_file.name in self.ingested_pdfs:
            print(f"{pdf_file.name} is already ingested.")
            return collection_name

        # Read the PDF file content into bytes
        pdf_bytes = pdf_file.read()

        # Create BytesIO objects for each method call
        pdf_stream1 = BytesIO(pdf_bytes)
        pdf_stream2 = BytesIO(pdf_bytes)

        # Extract all text and page-wise text from PDF in separate threads
        all_text_page_wise = await asyncio.to_thread(self.pdf.extract_all_text_page_wise, pdf_stream1)
        all_text = await asyncio.to_thread(self.pdf.extract_all_text, pdf_stream2)

        # Store the extracted text
        self.collection_texts[collection_name] = all_text

        # Store texts in RAG vector store in a separate thread
        await asyncio.to_thread(
            self.RAG.store_texts, all_text_page_wise, collection_name=collection_name
        )

        self.ingested_pdfs.append(pdf_file.name)

        return collection_name

    # ... Rest of the class remains unchanged ...


    async def generate_level_1(self, collection_name: str) -> dict:
        """
        Asynchronously generate Level 1 questions from the ingested collection.

        Args:
            collection_name (str): Name of the collection.

        Returns:
            dict: Generated topics and questions.
        """
        # Retrieve the extracted text
        all_text = self.collection_texts.get(collection_name)
        if not all_text:
            raise ValueError(f"No extracted text found for collection {collection_name}")

        # Generate topics and MCQs using OpenAI
        res = await self.openai.generate_topics_and_mcqs(context=all_text)

        return res

    async def generate_level_2(self, collection_name: str) -> dict:
        """
        Asynchronously generate Level 2 questions from the ingested collection using Retrieval-Augmented Generation (RAG).

        Args:
            collection_name (str): Name of the collection.

        Returns:
            dict: Metadata and generated questions.
        """
        # Retrieve the extracted text
        all_text_str = self.collection_texts.get(collection_name)
        if not all_text_str:
            raise ValueError(f"No extracted text found for collection {collection_name}")

        # Generate book information asynchronously
        book_info = await self.openai.generate_book_title(all_text_str)
        main_topics = book_info.get("main_topics", [])

        all_questions = []

        # Create a list of tasks for each topic to generate MCQs concurrently
        tasks = [
            self._process_topic(topic, collection_name)
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

    async def generate_chat_RAG(self, question, collection_name):
        """
        Generates an answer to a user's question using Retrieval-Augmented Generation (RAG).

        Args:
            question (str): The user's question.
            collection_name (str): Name of the collection.

        Returns:
            tuple: Answer from the LLM and the relevant documents.
        """
        # Fetch relevant documents for this question from this collection
        results, output = await asyncio.to_thread(
            self.RAG.fetch_relevant_documents, question, collection_name, top_k=3
        )

        context = await self._process_documents_context(output)
        ans = await self.openai.chat(context=context, question=question)

        return ans, output

    async def reset_data(self):
        """
        Resets the ingested data and clears the vector store.
        """
        self.ingested_pdfs = []
        self.collection_texts = {}
        await asyncio.to_thread(self.RAG.reset_client)

    async def _process_input_pdf(self, pdf_name: str) -> str:
        """
        Process the input PDF name to create a sanitized collection name.

        Args:
            pdf_name (str): Name of the input PDF file.

        Returns:
            str: Sanitized collection name.
        """
        # Replace spaces with underscores and remove other special characters
        # This regex keeps alphanumerics, underscores, and dots (for the extension)
        sanitized_pdf_name = re.sub(r'[^\w\.]', '_', pdf_name)
        sanitized_pdf_name = sanitized_pdf_name.replace(".", "_")

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

    async def _process_topic(self, topic: str, collection_name: str) -> list:
        """
        Asynchronously process a single topic to generate MCQs.

        Args:
            topic (str): The topic for which to generate questions.
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
