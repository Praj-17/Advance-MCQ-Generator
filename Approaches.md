Copy
# Tools & Frameworks
- Used Gemini 1.5-pro and flash models for question generation and chat.
- Used Gemini- text-Embeddings-004 for embedding generation
- Implemented RAG using Chroma DB for Level 2.
- Used [SimplerLLM](https://github.com/hassancs91/SimplerLLM) for Formatted json generation.
- Streamlit for [dashboard](https://advance-question-generator-streamlit.onrender.com) generation.
- FastAPI for API endpoints generation, [Swagger-UI](https://advance-question-generator-fastapi.onrender.com/docs) for testing endpoints.
- HTML for [FASTAPI Homepage](https://advance-question-generator-fastapi.onrender.com).
- Alternatively also created a [postman-collection](src/constants/Advance-MCQ-Generator.postman_collection.json) for the same api.
- Docker for contenarization,[ Github-actions](https://github.com/Praj-17/Advance-MCQ-Generator) and [Docker-Hub]() for CI/CD
- Render for Deployment
- Created Different images for [FASTAPI]( prajwal1717/advance-question-generator-fastapi:latest ) and [Streamlit](prajwal1717/advance-question-generator-streamlit:latest)

# Assumptions
1. Book format: Assumed PDF has consistent formatting, the PDF is not encrypted and contains mostly text
2. Images in PDF: Currently PDFs having all or most of the content in Images are not supported.
3. Topic granularity: Provided a high level defination of importatn topic in the  [topics_prompt](src/constants/level_1_topics.prompt)
4. Question complexity: Aimed for mixed difficulty levels

# Approach
Level 1:
- Used PDF extraction library [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/) for text processing and extraction
- Implemented topic extraction using LLMs (Gemini)
- Generated questions using LLMs (Gemini)

Level 2:
- Implemented RAG using ChromaDB
- Chunked text on page basis, each page has its own embedding for easy retrival and source indentification
- generated embeddings using Gemini text-embeddings-004 of size 768 each
- Cosine similarity for Vector search (inbuilt in chroma)

# Challenges & Solutions
1. - Challenge: Library conflicts
   - Description: The Libaries Simpler LLM and Openai had conflicting dependencies and the resolution was impossible
   - Solution:Shifted entire codebase from OpenAI to Gemini to resolve conflict


# Design Decisions
1. Chose all the aobve mentioned tools because I have good experience in them
2. Implemented fronted using Streamlit because it is intuitive and can be easily deployed on Render.

# Future Improvements
1. Add support for more question types
2. Improve answer verification
3. Enhance explanation generation
4. Add support for embedding, Chat models
5. Impement Local model, given more compute.
6. Implement more PDF related functionality like Google-Search, Entity Explainations, related-image support. 
7. Implement Celery + Redis Backend to set PDF ingestion as a background Task. 
