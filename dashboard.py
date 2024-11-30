import streamlit as st
import os
import time
import re
import json
import asyncio
import datetime  # Import datetime module for timestamps
from src.modules.AdvanceQuestionGenerator import AdvanceQuestionGeneratorClass  # Import the updated class

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
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None  # Store the uploaded file object
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Store chat interactions as list of dictionaries

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
            st.session_state.question_generator = AdvanceQuestionGeneratorClass(
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
        disabled=not st.session_state.api_key_valid or st.session_state.ingested_file is not None  # Disable uploader if API key is invalid or a file is already ingested
    )
    
    if uploaded_file and st.session_state.api_key_valid:
        st.session_state.uploaded_file = uploaded_file  # Store the uploaded file in session state
        st.info(f"📄 **{uploaded_file.name}** uploaded successfully.")
        
        with st.spinner(f"🔄 Ingesting **{uploaded_file.name}**..."):
            try:
                # Run the async ingestion
                collection_name = asyncio.run(st.session_state.question_generator.ingest_input_pdf(uploaded_file))
                st.success(f"✅ **{uploaded_file.name}** ingested into the vector store.")
                st.session_state.ingested_file = uploaded_file.name
                st.session_state.collection_name = collection_name
            except Exception as e:
                st.error(f"❌ Failed to ingest **{uploaded_file.name}**: {e}")
                st.session_state.uploaded_file = None  # Reset the uploaded file
        
        st.markdown(f"**File ingested:** {st.session_state.ingested_file}")
    elif st.session_state.ingested_file and st.session_state.api_key_valid:
        st.info(f"✅ **{st.session_state.ingested_file}** is already ingested. Ready to ask questions.")
    elif not st.session_state.api_key_valid:
        st.info("🔒 **Upload functionalities are disabled until a valid API Key is provided.**")
    
    # Reset Ingested Data Button
    st.markdown("---")
    st.header("🗑️ Reset Ingested Data")
    if st.session_state.api_key_valid and st.session_state.ingested_file:
        if st.button("Reset Ingested Data"):
            # Clear all session state variables
            st.session_state.clear()
            # Rerun the app after reset
            st.rerun()
    else:
        st.info("🔒 **Reset functionality is disabled until data is ingested.**")
    
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
    ["💬 Chat", "🟢 Level 1", "🟢 Level 2", "❓ FAQs", "📄 Sample Outputs", "📞 Contact Me"]
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
            st.session_state.chat_history = []
            st.rerun()
        
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
                                # Display each document without using an expander
                                st.markdown(f"**Segment {idx + 1}:**")
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

        # Handle chat input
        prompt = st.chat_input(placeholder="Type your question here...")
        if prompt:
            normalized_prompt = normalize_text(prompt)
            is_greeting = normalized_prompt in greeting_responses

            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            if is_greeting:
                response = greeting_responses[normalized_prompt]
                documents = []
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
                        response = answer_data.get('answer', 'No answer provided.')
                    except Exception as e:
                        st.error(f"❌ Error getting answer: {e}")
                        response = "I'm sorry, I couldn't process your request."
                        documents = []

            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "documents": documents if not is_greeting else []
            })

            # Append to chat history
            st.session_state.chat_history.append({
                "input": prompt,
                "output": response,
                "segments": documents if not is_greeting else [],
                "timestamp": datetime.datetime.now().isoformat()
            })

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for word in response_generator(response):
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
                        # Display each document without using an expander
                        st.markdown(f"**Segment {idx + 1}:**")
                        st.json({"source": doc})
            elif not is_greeting:
                st.write("ℹ️ No relevant segments found.")
        
        # Now, after processing the new input, we can display the download button
        if st.session_state.chat_history:
            chat_history_json = json.dumps(st.session_state.chat_history, indent=4, default=str)
            st.download_button(
                label="📥 Download Chat History",
                data=chat_history_json,
                file_name="chat_history.json",
                mime="application/json"
            )

# Level 1 Generation tab
with tab_level1:
    st.header("🟢 Generate Level 1 Questions")
    
    if not st.session_state.ingested_file:
        st.warning("⚠️ Please upload and process a PDF file in the sidebar before generating questions.")
    else:
        # Clear outputs button
        if st.button("🗑️ Clear Level 1 Output"):
            st.session_state.level_1_result = None
            st.rerun()
        
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
            st.rerun()
        
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
        {"question": "How do I delete all the ingested data?", "answer": "Use the 'Reset Ingested Data' button in the sidebar to clear all ingested data, including the uploaded PDF and any generated content."},
        {"question": "Why is there only one collection?", "answer": "The application is designed to handle only one PDF at a time for simplicity."},
        {"question": "Can I change the model and temperature?", "answer": "Yes, use the configurations in the sidebar to select the model and set the temperature."},
    ]
    
    for faq in faqs:
        with st.expander(f"Q: {faq['question']}"):
            st.write(f"A: {faq['answer']}")

# Sample Outputs tab
with tab_samples:
        # Sample PDF download link
    pdf_url = "https://file.notion.so/f/f/4e5eef6f-0e71-4510-94ea-9060620f5b8d/430448d6-64c6-4747-950b-bb7972032c72/Project_Management.pdf?table=block&id=14a6b20a-8ac1-80dd-ad9c-dfaee829d20b&spaceId=4e5eef6f-0e71-4510-94ea-9060620f5b8d&expirationTimestamp=1733061600000&signature=-nOP1Nw3VvUkVRTL4XcrZQbcllBNCB14E-W56ZVUUP0&downloadName=Project+Management.pdf"
    st.markdown(f"[📥 Download Sample PDF]({pdf_url})")
    st.header("📄 Sample Outputs for All Tabs")
    
    # Placeholders for JSON file paths
    sample_chat_json_path = "src/constants/chat_history.json"
    sample_level1_json_path = "src/constants/level_1_questions_Project_Management.pdf.json"
    sample_level2_json_path = "src/constants/level_2_questions_Project_Management.pdf.json"
    
    # Sample Chat Outputs
    st.subheader("💬 Sample Chat Outputs")
    if os.path.exists(sample_chat_json_path):
        with open(sample_chat_json_path, 'r', encoding='utf-8') as f:
            sample_chat = json.load(f)
        with st.expander("View Sample Chat JSON"):
            st.json(sample_chat)
    else:
        st.info("ℹ️ Sample chat JSON file not found. Please ensure the path is correct.")
    
    # Sample Level 1 Outputs
    st.subheader("🟢 Sample Level 1 Outputs")
    if os.path.exists(sample_level1_json_path):
        with open(sample_level1_json_path, 'r', encoding='utf-8') as f:
            sample_level1 = json.load(f)
        with st.expander("View Sample Level 1 JSON"):
            st.json(sample_level1)
    else:
        st.info("ℹ️ Sample Level 1 JSON file not found. Please ensure the path is correct.")
    
    # Sample Level 2 Outputs
    st.subheader("🟢 Sample Level 2 Outputs")
    if os.path.exists(sample_level2_json_path):
        with open(sample_level2_json_path, 'r', encoding='utf-8') as f:
            sample_level2 = json.load(f)
        with st.expander("View Sample Level 2 JSON"):
            st.json(sample_level2)
    else:
        st.info("ℹ️ Sample Level 2 JSON file not found. Please ensure the path is correct.")
    

# Contact tab
with tab_contact:
    st.header("📞 Contact Information")
    st.write("Feel free to reach out through any of the following platforms 😊:")
    
    st.markdown("### 📧 Email")
    st.write("pwaykos1@gmail.com")
    
    st.markdown("### 📱 Phone")
    st.write("+1 724-954-2810")
    
    st.markdown("### 🔗 LinkedIn")
    st.markdown("[![LinkedIn](https://img.icons8.com/color/48/000000/linkedin.png)](https://www.linkedin.com/in/prajwal-waykole-3b5b00167/)")
    
    st.markdown("### 🐙 GitHub")
    st.markdown("[![GitHub](https://img.icons8.com/ios-glyphs/30/000000/github.png)](https://github.com/praj-17)")
    
    st.markdown("### 📄 Resume")
    st.markdown("[![Resume](https://img.icons8.com/doodle/48/000000/resume.png)](https://drive.google.com/file/d/1OiSCu4e_1R7cawKSU80cr63Cd2-4OVq7/view?usp=drivesdk)")
