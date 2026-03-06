import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Personal Chatbot - About Me",
    page_icon="👤",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        text-align: right;
    }
    .bot-message {
        background-color: #f1f1f1;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)

# Set your OpenRouter API key
os.environ["OPENROUTER_API_KEY"] = "YOUR_OPENROUTER_API_KEY_HERE"  # Replace with your key

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'personal_info' not in st.session_state:
    st.session_state.personal_info = {}
if 'info_provided' not in st.session_state:
    st.session_state.info_provided = False

# Title
st.title("👤 Personal Chatbot - All About Me")
st.markdown("Ask me anything about myself and I'll answer!")

# Sidebar for personal information input
with st.sidebar:
    st.header("📝 Tell Me About Yourself")
    
    with st.form("personal_info_form"):
        name = st.text_input("Your Name", placeholder="John Doe")
        age = st.number_input("Your Age", min_value=1, max_value=120, value=25)
        location = st.text_input("Where do you live?", placeholder="New York, USA")
        occupation = st.text_input("Your Occupation", placeholder="Software Engineer")
        education = st.text_input("Your Education", placeholder="Bachelor's in Computer Science")
        hobbies = st.text_area("Your Hobbies", placeholder="Reading, coding, hiking...")
        skills = st.text_area("Your Skills", placeholder="Python, JavaScript, Communication...")
        favorite_food = st.text_input("Favorite Food", placeholder="Pizza")
        favorite_movie = st.text_input("Favorite Movie", placeholder="Inception")
        favorite_book = st.text_input("Favorite Book", placeholder="The Alchemist")
        goals = st.text_area("Your Goals", placeholder="Become a senior developer...")
        fun_fact = st.text_input("A Fun Fact About You", placeholder="I can speak 3 languages...")
        
        # Model selection
        model_choice = st.selectbox(
            "Choose Model",
            ["openai/gpt-3.5-turbo", "openai/gpt-4", "google/gemini-pro", "anthropic/claude-2"],
            index=0
        )
        
        submitted = st.form_submit_button("Save My Information")
        
        if submitted:
            st.session_state.personal_info = {
                "name": name,
                "age": age,
                "location": location,
                "occupation": occupation,
                "education": education,
                "hobbies": hobbies,
                "skills": skills,
                "favorite_food": favorite_food,
                "favorite_movie": favorite_movie,
                "favorite_book": favorite_book,
                "goals": goals,
                "fun_fact": fun_fact,
                "model": model_choice,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.info_provided = True
            st.success("Information saved! Start chatting!")
    
    if st.session_state.info_provided:
        st.header("📋 Your Information")
        for key, value in st.session_state.personal_info.items():
            if key not in ["last_updated", "model"] and value:
                st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
        st.caption(f"Model: {st.session_state.personal_info.get('model', 'Not selected')}")
        st.caption(f"Last updated: {st.session_state.personal_info['last_updated']}")
        
        if st.button("Clear Information"):
            st.session_state.personal_info = {}
            st.session_state.info_provided = False
            st.session_state.messages = []
            st.rerun()

# Main chat area
if st.session_state.info_provided:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about myself..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Create a prompt template
                template = """
                You are a personal chatbot that answers questions about the person whose information is provided below.
                Only answer questions based on the information provided. If the question is about something not in the 
                information, politely say you don't have that information.
                
                PERSONAL INFORMATION:
                {personal_info}
                
                QUESTION: {question}
                
                Answer in a friendly, conversational way as if you are the person. Be concise but helpful.
                """
                
                # Format personal info as a string
                info_str = "\n".join([f"{k}: {v}" for k, v in st.session_state.personal_info.items() 
                                     if v and k not in ["last_updated", "model"]])
                
                # Create prompt
                prompt_template = ChatPromptTemplate.from_template(template)
                
                # Initialize LLM with OpenRouter
                llm = ChatOpenAI(
                    model=st.session_state.personal_info.get("model", "openai/gpt-3.5-turbo"),
                    openai_api_key=os.environ["OPENROUTER_API_KEY"],
                    openai_api_base="https://openrouter.ai/api/v1",
                    temperature=0.7
                )
                
                # Create chain
                chain = prompt_template | llm | StrOutputParser()
                
                # Get response
                response = chain.invoke({
                    "personal_info": info_str,
                    "question": prompt
                })
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.info("👈 Please fill in your information in the sidebar to start chatting!")
    
    st.markdown("""
    ### How it works:
    1. Get a free API key from [OpenRouter.ai](https://openrouter.ai/)
    2. Fill in your personal information in the sidebar
    3. Choose your preferred AI model
    4. Click "Save My Information"
    5. Start asking questions about yourself!
    """)

st.markdown("---")
st.caption("Personal Chatbot - Powered by OpenRouter")