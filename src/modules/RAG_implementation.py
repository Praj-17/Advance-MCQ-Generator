import os
import sys
from typing import Dict, Any, List, Optional

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import json

# Import LangChain's OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings

load_dotenv()


class ChromaVectorStore:
    """
    A class to handle storing and querying documents in Chroma Vector Store using LangChain's OpenAI embeddings.
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY"),
        chroma_db_impl: str = "duckdb+parquet",
        persist_directory: str = "./data/chroma_db",
        embedding_model: str = "text-embedding-ada-002",
    ):
        """
        Initializes the ChromaVectorStore with the provided configurations.

        :param openai_api_key: Your OpenAI API key. If None, it will be fetched from the OPENAI_API_KEY environment variable.
        :param chroma_db_impl: Implementation of the Chroma database. Defaults to 'duckdb+parquet'.
        :param persist_directory: Directory where Chroma will persist the database.
        :param embedding_model: The OpenAI embedding model to use.
        """
        # Set OpenAI API key
        if openai_api_key:
            self.openai_api_key = openai_api_key
        else:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            if not self.openai_api_key:
                raise ValueError(
                    "OpenAI API key not provided and OPENAI_API_KEY environment variable not set."
                )
        if self.openai_api_key:
            # Initialize LangChain's OpenAIEmbeddings
            self.embeddings = OpenAIEmbeddings(
                api_key=self.openai_api_key,
                model=embedding_model
            )
        else:
            self.embeddings = None

        self.embeddings_model_name = embedding_model
        self.method = "RAG Pipeline"
        self.vector_store = "Chroma"

        # Initialize Chroma client
        self.chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(allow_reset  = True)
            
        )

    def get_or_create_collection(self, collection_name: str):
        """
        Retrieves an existing collection or creates a new one if it doesn't exist.

        :param collection_name: The name of the collection to retrieve or create.
        :return: The Chroma collection object.
        """
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            print(f"Using existing collection: '{collection_name}'")
        except Exception:
            collection = self.chroma_client.create_collection(name=collection_name)
            print(f"Created new collection: '{collection_name}'")
        return collection

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates an embedding for the given text using LangChain's OpenAIEmbeddings.

        :param text: The text to embed.
        :return: A list of floats representing the embedding.
        """
        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            print(f"Error generating embedding with LangChain: {e}")
            raise

    def store_texts(self, pages: Dict[int, str], collection_name: str) -> None:
        """
        Stores text data from pages into the specified Chroma vector store collection with embeddings and metadata.

        :param pages: A dictionary with page numbers as keys and text content as values.
        :param collection_name: The name of the collection where documents will be stored.
        """
        collection = self.get_or_create_collection(collection_name)

        # Fetch existing IDs to avoid duplicates
        try:
            existing_docs = collection.get(ids=[f"page_{page_num}" for page_num in pages.keys()])
            existing_ids = set(existing_docs["ids"])
        except Exception as e:
            print(f"Error fetching existing document IDs: {e}")
            existing_ids = set()

        texts = []
        embeddings = []
        metadatas = []
        ids = []

        for page_num, text in pages.items():
            doc_id = f"page_{page_num}"
            if doc_id in existing_ids:
                print(f"Document with ID '{doc_id}' already exists. Skipping to avoid duplicates.")
                continue  # Skip adding this document

            if not text.strip():
                print(f"Warning: Page {page_num} is empty. Skipping.")
                continue
            try:
                embedding = self.get_embedding(text)
            except Exception as e:
                print(f"Failed to generate embedding for page {page_num}: {e}")
                continue
            embeddings.append(embedding)
            texts.append(text)
            metadatas.append({"page_number": page_num})
            ids.append(doc_id)

        if texts:
            try:
                collection.add(
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids,
                )
                print(f"Successfully added {len(texts)} documents to collection '{collection_name}'.")
            except Exception as e:
                print(f"Error adding documents to collection '{collection_name}': {e}")
        else:
            print(f"No valid texts to add to collection '{collection_name}'.")

    def fetch_relevant_documents(
        self, topic: str, collection_name: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetches top_k relevant documents from the specified Chroma collection based on the topic.

        :param topic: The topic to search for.
        :param collection_name: The name of the collection to query.
        :param top_k: The number of top documents to retrieve.
        :return: A tuple containing the raw results and a list of dictionaries with the document, metadata, and confidence score.
        """
        collection = self.get_or_create_collection(collection_name)

        try:
            query_embedding = self.get_embedding(topic)
        except Exception as e:
            print(f"Failed to generate embedding for the topic: {e}")
            raise

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "distances", "documents"]
            )
        except Exception as e:
            print(f"Error querying the Chroma collection '{collection_name}': {e}")
            raise

        fetched_docs = []
        # Access the first (and only) query's results
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for doc, metadata, distance in zip(documents, metadatas, distances):
            confidence = max(0.0, 1.0 - distance)  # Simple normalization
            fetched_docs.append(
                {
                    "document": doc,
                    "metadata": metadata,
                    "confidence": round(confidence, 4),
                }
            )

        return results, fetched_docs

    def reset_client(self):
        return self.chroma_client.reset()

if __name__ == "__main__":
    try:
        chroma_store = ChromaVectorStore()
        pdf_name = "Project_Management_pdf"

        # Load data from 'extracted_data.json'
        with open("extracted_data.json", "r") as f:
            data = json.load(f)

        # Store texts into the Chroma collection
        chroma_store.store_texts(data, collection_name=pdf_name)

        query = "Project Manager"

        # Fetch relevant documents using the correct method name
        results, output = chroma_store.fetch_relevant_documents(query, pdf_name)
        print(output)

        # Save outputs to JSON files
        with open("RAG_output.json", "w") as f:
            json.dump(output, f, indent=4)

        with open("results.json", "w") as f:
            json.dump(results, f, indent=4)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
