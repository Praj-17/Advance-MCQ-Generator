import streamlit as st
import os
import time
import re
import json
import asyncio
from main import AdvanceQuestionGenerator  # Import the updated class

# Set page configuration
st.set_page_config(
    page_title="📄🤖 Interactive PDF Q&A Chatbot",
    page_icon="📄🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
    <style>
        /* Hide the main menu and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        /* Customize the header */
        .css-1d391kg {
            background-color: #f0f2f6;
        }
        /* Customize buttons */
        .stButton>button {
            color: white;
            background-color: #4CAF50;
        }
        /* Customize sidebar */
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
    </style>
    """, unsafe_allow_html=True)

st.title("📄🤖 Interactive PDF Q&A Chatbot")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ingested_file" not in st.session_state:
    st.session_state.ingested_file = None
if "collection_name" not in st.session_state:
    st.session_state.collection_name = None
if "question_generator" not in st.session_state:
    st.session_state.question_generator = None  # Initialize as None
if "level_1_result" not in st.session_state:
    st.session_state.level_1_result = None
if "level_2_result" not in st.session_state:
    st.session_state.level_2_result = None
if "OPENAI_API_KEY" not in st.session_state:
    st.session_state.OPENAI_API_KEY = None
if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = False
if "model_name" not in st.session_state:
    st.session_state.model_name = "gpt-4o-mini"  # Default model name set to 'gpt-4o-mini'
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7  # Default temperature

# Sidebar for API Key Input and PDF upload
with st.sidebar:
    st.header("🔐 **OpenAI API Key**")
    
    # API Key Input Field
    api_key_input = st.text_input(
        "Enter your OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="Your API key is used to access OpenAI's services. It is not stored or shared.",
        value=st.session_state.get("OPENAI_API_KEY", "")  # Persist the API key input
    )
    
    # Validate API Key
    if api_key_input:
        if api_key_input.startswith("sk-"):
            st.session_state["OPENAI_API_KEY"] = api_key_input
            st.session_state["api_key_valid"] = True
            os.environ["OPENAI_API_KEY"] = api_key_input  # Set environment variable for use in the app
            st.success("✅ **API Key is valid and has been set.**")
        else:
            st.session_state["api_key_valid"] = False
            st.error("❌ **Invalid API Key.** It should start with `sk-`.")
    else:
        st.session_state["api_key_valid"] = False
        st.warning("⚠️ **Please enter your OpenAI API Key to enable functionalities.**")
    
    st.markdown("---")
    
    # Configuration Settings
    st.header("⚙️ Configurations")
    
    # Model Selection
    model_options = ["gpt-4o", "gpt-4o-mini"]
    model_name = st.selectbox(
        "Select Model",
        options=model_options,
        index=model_options.index(st.session_state.get("model_name", "gpt-4o-mini"))  # Default to 'gpt-4o-mini'
    )
    st.session_state.model_name = model_name
    
    # Temperature Slider
    temperature = st.slider(
        "Select Temperature",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.get("temperature", 0.7),
        step=0.1,
        help="Controls the randomness of the model's output. 0 is deterministic, 1 is very random."
    )
    st.session_state.temperature = temperature
    
    st.markdown("---")
    
    st.header("📥 Upload and Process PDF")
    
    # Instantiate AdvanceQuestionGenerator with the API key and configurations
    if st.session_state.api_key_valid:
        if st.session_state.question_generator is None:
            st.session_state.question_generator = AdvanceQuestionGenerator(
                openai_key=st.session_state.OPENAI_API_KEY,
                model_name=st.session_state.model_name,
                temperature=st.session_state.temperature
            )
        else:
            # Update the existing instance with new configurations
            st.session_state.question_generator.openai.openai_key = st.session_state.OPENAI_API_KEY
            st.session_state.question_generator.openai.model_name = st.session_state.model_name
            st.session_state.question_generator.openai.temperature = st.session_state.temperature
    
    # File uploader - Limited to single file
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        accept_multiple_files=False,  # Set to False to limit to single file
        help="Upload a PDF file for processing.",
        disabled=not st.session_state.api_key_valid  # Disable uploader if API key is invalid
    )
    
    if uploaded_file and st.session_state.api_key_valid:
        temp_dir = os.getenv("TEMP_FILE_DIRECTORY", "temp_files")
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, uploaded_file.name)
        
        # Save the uploaded file to the temp directory
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.info(f"📄 **{uploaded_file.name}** uploaded successfully.")
        
        with st.spinner(f"🔄 Ingesting **{uploaded_file.name}**..."):
            try:
                # Run the async ingestion
                collection_name = asyncio.run(st.session_state.question_generator.ingest_input_pdf(file_path))
                st.success(f"✅ **{uploaded_file.name}** ingested into the vector store.")
                st.session_state.ingested_file = uploaded_file.name
                st.session_state.collection_name = collection_name
            except Exception as e:
                st.error(f"❌ Failed to ingest **{uploaded_file.name}**: {e}")
        
        # Optionally, remove the file after ingestion
        try:
            os.remove(file_path)
        except Exception as e:
            st.warning(f"⚠️ Could not delete temporary file **{uploaded_file.name}**: {e}")
        
        st.markdown(f"**File ingested:** {st.session_state.ingested_file}")
    elif st.session_state.ingested_file and st.session_state.api_key_valid:
        st.info(f"✅ **{st.session_state.ingested_file}** is already ingested. Ready to ask questions.")
    elif not st.session_state.api_key_valid:
        st.info("🔒 **Upload functionalities are disabled until a valid API Key is provided.**")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This application allows you to upload a PDF file, process it, interactively ask questions, and generate MCQ questions based on the content of the PDF.
    The application uses OpenAI's API services to power the LLM use case.
    """)
    st.markdown("---")
    st.markdown("### 💻 Deployment Considerations")
    st.markdown("""
    The application relies on APIs because it is being hosted on a server with 512MB of RAM and 1GB storage. Therefore, the usage of any local models like Ollama or HF is not feasible.
    
    However, given a significant amount of compute, we can always use local models as needed.
    """)

# Define tabs
tab_chat, tab_level1, tab_level2, tab_faqs, tab_samples, tab_contact = st.tabs(
    ["💬 Chat", "🟢 Level 1", "🟢 Level 2", "❓ FAQs", "📄 Sample Queries", "📞 Contact Me"]
)

# Chat tab
with tab_chat:
    st.header("💬 Chat with Your PDF")
    
    if not st.session_state.api_key_valid or not st.session_state.question_generator:
        st.error("⚠️ Please provide a valid OpenAI API Key to use the chat functionality.")
    elif not st.session_state.ingested_file:
        st.error("⚠️ Please upload and process a PDF file first.")
    else:
        # Clear outputs button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.experimental_rerun()
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and "documents" in message:
                    if message["documents"]:
                        st.markdown("**📄 Relevant Document Segments:**")
                        num_cols = 2
                        cols = st.columns(num_cols)
                        for idx, doc in enumerate(message['documents']):
                            col = cols[idx % num_cols]
                            with col:
                                with st.expander(f"📄 Segment {idx + 1}"):
                                    # Display each document as JSON with a 'source' key
                                    st.json({"source": doc})
                    else:
                        st.write("ℹ️ No relevant segments found.")

        # Chat input
        def response_generator(response):
            for word in response.split():
                yield word + " "
                time.sleep(0.05)

        def normalize_text(text):
            return re.sub(r'[^\w\s]', '', text).lower().strip()

        greeting_responses = {
            "hi": "👋 Hello! How can I assist you today?",
            "hello": "👋 Hello! What can I do for you?",
            "hey": "👋 Hey there! How can I help?",
            "good morning": "🌅 Good morning! What can I assist you with?",
            "good afternoon": "☀️ Good afternoon! How can I help you today?",
            "good evening": "🌙 Good evening! How may I assist you?"
        }

        if prompt := st.chat_input(placeholder="Type your question here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            normalized_prompt = normalize_text(prompt)

            if normalized_prompt in greeting_responses:
                response = greeting_responses[normalized_prompt]
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)
            else:
                with st.spinner("🤔 Thinking..."):
                    try:
                        # Call the generate_chat_RAG method
                        # Assuming generate_chat_RAG returns (answer_data, documents)
                        answer_data, documents = asyncio.run(
                            st.session_state.question_generator.generate_chat_RAG(
                                prompt, st.session_state.collection_name
                            )
                        )
                        answer = answer_data.get('answer', 'No answer provided.')
                    except Exception as e:
                        st.error(f"❌ Error getting answer: {e}")
                        answer = "I'm sorry, I couldn't process your request."
                        documents = []

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "documents": documents
                })

                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    for word in response_generator(answer):
                        full_response += word
                        message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)

                if documents:
                    st.markdown("**📄 Relevant Document Segments:**")
                    num_cols = 2
                    cols = st.columns(num_cols)
                    for idx, doc in enumerate(documents):
                        col = cols[idx % num_cols]
                        with col:
                            with st.expander(f"📄 Segment {idx + 1}"):
                                # Display each document as JSON with a 'source' key
                                st.json({"source": doc})
                else:
                    st.write("ℹ️ No relevant segments found.")

# Level 1 Generation tab
with tab_level1:
    st.header("🟢 Generate Level 1 Questions")
    
    if not st.session_state.ingested_file:
        st.warning("⚠️ Please upload and process a PDF file in the sidebar before generating questions.")
    else:
        # Clear outputs button
        if st.button("🗑️ Clear Level 1 Output"):
            st.session_state.level_1_result = None
            st.experimental_rerun()
        
        # Disable the button if API key is invalid
        generate_level1_disabled = not st.session_state.api_key_valid or not st.session_state.question_generator
        
        if generate_level1_disabled:
            st.info("🔒 **Provide a valid OpenAI API Key to enable this functionality.**")
        
        if st.button("Generate Level 1", disabled=generate_level1_disabled):
            with st.spinner("🔄 Generating Level 1 questions..."):
                try:
                    # Call generate_level_1
                    level_1_result = asyncio.run(
                        st.session_state.question_generator.generate_level_1(
                            st.session_state.collection_name
                        )
                    )
                    st.session_state.level_1_result = level_1_result
                    
                    st.success("✅ Level 1 questions generated successfully.")
                except Exception as e:
                    st.error(f"❌ Failed to generate Level 1 questions: {e}")
                    st.session_state.level_1_result = None
        
        # Display the Level 1 result if available
        if st.session_state.level_1_result:
            st.markdown("### 📊 Level 1 JSON Results")
            st.json(st.session_state.level_1_result)
            
            # Optionally, allow downloading the results
            json_output = json.dumps(st.session_state.level_1_result, indent=4)
            st.download_button(
                label="📥 Download Level 1 Questions",
                data=json_output,
                file_name=f"level_1_questions_{st.session_state.collection_name}.json",
                mime="application/json"
            )

# Level 2 Generation tab
with tab_level2:
    st.header("🟢 Generate Level 2 Questions")
    
    if not st.session_state.ingested_file:
        st.warning("⚠️ Please upload and process a PDF file in the sidebar before generating questions.")
    else:
        # Clear outputs button
        if st.button("🗑️ Clear Level 2 Output"):
            st.session_state.level_2_result = None
            st.experimental_rerun()
        
        # Disable the button if API key is invalid
        generate_level2_disabled = not st.session_state.api_key_valid or not st.session_state.question_generator
        
        if generate_level2_disabled:
            st.info("🔒 **Provide a valid OpenAI API Key to enable this functionality.**")
        
        if st.button("Generate Level 2", disabled=generate_level2_disabled):
            with st.spinner("🔄 Generating Level 2 questions..."):
                try:
                    # Call the generate_level_2 method
                    result = asyncio.run(
                        st.session_state.question_generator.generate_level_2(
                            st.session_state.collection_name
                        )
                    )
                    
                    # Store Level 2 results in session state
                    st.session_state.level_2_result = result
                    
                    st.success("✅ Level 2 questions generated successfully.")
                except Exception as e:
                    st.error(f"❌ Failed to generate Level 2 questions: {e}")
                    st.session_state.level_2_result = None
        
        # Display the Level 2 result if available
        if st.session_state.level_2_result:
            st.markdown("### 📊 Level 2 JSON Results")
            st.json(st.session_state.level_2_result)
            
            # Optionally, allow downloading the results
            json_output = json.dumps(st.session_state.level_2_result, indent=4)
            st.download_button(
                label="📥 Download Level 2 Questions",
                data=json_output,
                file_name=f"level_2_questions_{st.session_state.collection_name}.json",
                mime="application/json"
            )

# FAQs tab
with tab_faqs:
    st.header("❓ Frequently Asked Questions")
    st.markdown("Here are some frequently asked questions:")
    
    faqs = [
        {"question": "How do I upload a PDF file?", "answer": "Use the file uploader in the sidebar to upload your PDF file."},
        {"question": "How do I ask a question about the PDF?", "answer": "Type your question in the chat input at the bottom of the Chat tab."},
        {"question": "How do I delete all the ingested data?", "answer": "You will have to delete the folder `chroma` manually from the code-base."},
        {"question": "Why is there only one collection?", "answer": "The application is designed to handle only one PDF at a time for simplicity."},
        {"question": "Can I change the model and temperature?", "answer": "Yes, use the configurations in the sidebar to select the model and set the temperature."},
    ]
    
    for faq in faqs:
        with st.expander(f"Q: {faq['question']}"):
            st.write(f"A: {faq['answer']}")

# Sample Queries tab
with tab_samples:
    st.header("📄 Sample Queries")
    
    json_file_path = "src/constants/example_queries.json"
    
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                sample_queries = json.load(f)
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON file. Please check the file format.")
            sample_queries = []
    else:
        st.warning(f"⚠️ JSON file not found at path: `{json_file_path}`")
        sample_queries = []
    
    pdf_url = "https://github.com/Praj-17/PDF-RAG-LLAMA/blob/main/Data/IARC%20Sci%20Pub%20163_Chapter%203.pdf"
    st.markdown(f"[📥 Download Sample PDF]({pdf_url})")
    
    if sample_queries:
        st.markdown("### 📚 Here are some sample queries and their answers created from the above PDF:")
    
        for query in sample_queries:
            st.subheader(f"Q: {query['question']}")
            st.write(f"A: {query['answer']}")
            if query.get('documents'):
                st.markdown("**📄 Relevant Document Segments:**")
                num_cols = 3
                cols = st.columns(num_cols)
                for doc in query['documents']:
                    col = cols[doc['index'] % num_cols]
                    with col:
                        with st.expander(f"📄 Segment {doc['index'] + 1}"):
                            st.write(doc['text'])
            else:
                st.write("ℹ️ No relevant segments found.")
    else:
        st.info("ℹ️ No sample queries to display. Please ensure the JSON file path is correct and the file is properly formatted.")

# Contact tab
with tab_contact:
    st.header("📞 Contact Information")
    st.write("Feel free to reach out through any of the following platforms 😊:")
    
    st.markdown("### 📧 Email")
    if st.button("✉️ Send Email"):
        st.write("mailto:pwaykos1@gmail.com")
    
    st.markdown("### 📱 Phone")
    if st.button("📞 Call 724-954-2810"):
        st.write("tel:+17249542810")
    
    st.markdown("### 🔗 LinkedIn")
    st.markdown("[![LinkedIn](https://img.icons8.com/color/48/000000/linkedin.png)](https://www.linkedin.com/in/your-linkedin-profile)")
    
    st.markdown("### 🐙 GitHub")
    st.markdown("[![GitHub](https://img.icons8.com/ios-glyphs/30/000000/github.png)](https://github.com/praj-17)")
    
    st.markdown("### 📄 Resume")

    st.markdown("[![Resume](https://img.icons8.com/doodle/48/000000/resume.png)](https://drive.google.com/file/d/1OiSCu4e_1R7cawKSU80cr63Cd2-4OVq7/view?usp=drivesdk)")
