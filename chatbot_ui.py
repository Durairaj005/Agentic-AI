import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_NAME = "Rajan"
CREATOR_NAME = "Durai"
CREATOR_INFO = "a software developer passionate about building helpful AI tools"

MASTER_PROMPT = f"""நீ {BOT_NAME} — ஒரு super funny, heart-warming cooking assistant மற்றும் timepass chat buddy! உன்னை உருவாக்கியவர் {CREATOR_NAME}, {CREATOR_INFO}.

🗣️ LANGUAGE:
- Always reply in a fun mix of Tamil and English (Tanglish). Example: "Dei, that sambar smells like heaven da! 😂"
- Never reply in pure English or pure formal Tamil. Keep it natural and street-style.

😂 TONE & PERSONALITY:
- You are FUNNY, playful, and lovable like a best friend who also knows cooking.
- Use emojis generously 😂🍳❤️😍🤣 in every reply.
- Crack jokes, funny comparisons, light sarcasm — but always kind-hearted.
- You are NOT a tech bot, NOT a coding assistant. You are a kitchen hero and chill timepass companion.

🍛 FOCUS TOPICS:
- PRIMARY: Cooking tips, recipes, kitchen hacks, ingredient substitutions, food facts.
- SECONDARY: Funny general knowledge, fun facts, timepass chat, jokes, light banter.
- If someone asks something outside cooking or general knowledge (like coding, math, serious tech), gently redirect: "Ayyo da, naan kitchen-la iruken, office-la illa 😅 Ask me about food!"

📏 RESPONSE LENGTH:
- Match the user's energy. Short question → short funny reply. Long question → detailed helpful reply with jokes mixed in.
- Never give boring bullet-point lists. Make it feel like a fun conversation.

😤 HANDLING RUDE / ANGRY USERS:
- Never get angry back. Stay calm, warm, and extra funny 😂.
- Respond with a funny comparison or imaginary meme. Example: "Bro, you're angrier than a pressure cooker on full flame 😂 Chill da, have some chai ☕"
- Gently bring them back to a good mood with humor.

🚫 RESTRICTIONS:
- Don't avoid any question — answer everything but keep it as general knowledge level. No hardcore technical deep dives.
- Never be rude, mean, or offensive even if provoked.
- Never break character as {BOT_NAME}.
- If asked who made you: proudly say {CREATOR_NAME} made you! 🎉

Remember: You are the fun friend everyone wishes they had in the kitchen! 🍳❤️
"""

MODEL = "openai/gpt-4o-mini"

# Page Configuration
st.set_page_config(
    page_title=f"{BOT_NAME}'s Kitchen & Chat 🍳",
    page_icon="🍳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Beautiful UI
st.markdown("""
<style>
    /* Main background gradient */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 1rem 1rem 1rem;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { box-shadow: 0 10px 30px rgba(240, 147, 251, 0.4); }
        to { box-shadow: 0 10px 40px rgba(245, 87, 108, 0.6); }
    }
    
    .main-header h1 {
        color: white;
        font-size: 3em;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        font-weight: bold;
    }
    
    .main-header p {
        color: #ffffffee;
        font-size: 1.2em;
        margin-top: 0.5rem;
    }
    
    /* Chat container */
    .chat-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        margin-bottom: 2rem;
        max-height: 500px;
        overflow-y: auto;
    }
    
    /* User message */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 1rem 0 1rem auto;
        max-width: 80%;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        animation: slideInRight 0.3s ease-out;
    }
    
    /* Bot message */
    .bot-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 1rem auto 1rem 0;
        max-width: 80%;
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
        animation: slideInLeft 0.3s ease-out;
    }
    
    @keyframes slideInRight {
        from { transform: translateX(50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Input box styling */
    .stTextInput > div > div > input {
        background: white;
        border: 3px solid #f093fb;
        border-radius: 25px;
        padding: 1rem 1.5rem;
        font-size: 1.1em;
        transition: all 0.3s;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #f5576c;
        box-shadow: 0 0 20px rgba(245, 87, 108, 0.5);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-size: 1.1em;
        font-weight: bold;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(245, 87, 108, 0.6);
    }
    
    /* Sidebar styling */
    .sidebar-info {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Welcome card */
    .welcome-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }
    
    .welcome-card h3 {
        color: #764ba2;
        margin-bottom: 1rem;
    }
    
    /* Scroll bar styling */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: white;
        font-size: 0.9em;
        margin-top: 2rem;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'client' not in st.session_state:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        st.session_state.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    else:
        st.session_state.client = None

def get_bot_response(user_message):
    """Get response from the bot"""
    if not st.session_state.client:
        return "❌ Ayyo! API key missing da! Tell admin to add OPENROUTER_API_KEY 😅"
    
    history = [{"role": "system", "content": MASTER_PROMPT}]
    for msg in st.session_state.messages:
        history.append({"role": msg["role"], "content": msg["content"]})
    history.append({"role": "user", "content": user_message})
    
    try:
        response = st.session_state.client.chat.completions.create(
            model=MODEL,
            max_tokens=1024,
            messages=history,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"😅 Ayyo! Something went wrong da! Error: {str(e)}"

# Header
st.markdown(f"""
<div class="main-header">
    <h1>🍳 {BOT_NAME}'s Kitchen & Chat Corner! 💖</h1>
    <p>❤️‍🔥 Where food meets fun & love meets laughter ❤️‍🔥</p>
    <p style="font-size: 0.9em; margin-top: 0.5rem;">Made with ❤️ by {CREATOR_NAME}</p>
</div>
""", unsafe_allow_html=True)

# Welcome screen if user hasn't entered name
if st.session_state.user_name is None:
    st.markdown("""
    <div class="welcome-card">
        <h3>😘 Welcome da! 😘</h3>
        <p style="font-size: 1.2em; color: #555;">Enter your name below to start chatting!</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_name = st.text_input("🌟 Your Name:", placeholder="Enter your name here...", label_visibility="collapsed")
        if st.button("🚀 Start Chatting!", use_container_width=True):
            if user_name.strip():
                st.session_state.user_name = user_name.strip()
                
                # Get welcome message
                opening = (
                    f"The user's name is {st.session_state.user_name}. "
                    f"Give a super fun, attractive, warm Tanglish welcome greeting using their name. "
                    f"Introduce yourself as {BOT_NAME}, a funny cooking assistant and timepass buddy made by {CREATOR_NAME}. "
                    f"Use lots of heart and kiss emojis 😘❤️💖🍳. Make it feel like a grand filmy entry. "
                    f"Then invite them to ask anything about cooking or just chill and chat."
                )
                welcome = get_bot_response(opening)
                st.session_state.messages.append({"role": "assistant", "content": welcome})
                st.rerun()
            else:
                st.warning("⚠️ Please enter your name first da! 😊")

else:
    # Chat interface
    st.markdown(f"### 👋 Hey {st.session_state.user_name}! Chat with {BOT_NAME} 💬")
    
    # Chat container
    chat_html = '<div class="chat-container">'
    for message in st.session_state.messages:
        if message["role"] == "user":
            chat_html += f'<div class="user-message">👤 {message["content"]}</div>'
        else:
            chat_html += f'<div class="bot-message">🍳 {message["content"]}</div>'
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)
    
    # Input area
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(
            "Type your message:",
            placeholder="Ask me about cooking or just chat! 😊",
            key="user_input",
            label_visibility="collapsed"
        )
    with col2:
        send_button = st.button("Send 📤", use_container_width=True)
    
    # Handle message sending
    if send_button and user_input.strip():
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get bot response
        bot_response = get_bot_response(user_input)
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        
        st.rerun()
    
    # Action buttons
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.messages = []
            st.session_state.user_name = None
            st.rerun()
    with col3:
        if st.button("ℹ️ About", use_container_width=True):
            st.info(f"""
            **{BOT_NAME}** is your friendly cooking assistant and timepass buddy! 🍳❤️
            
            - Ask cooking questions 🥘
            - Get recipe tips 📖
            - Just chill and chat 😎
            
            Made with ❤️ by **{CREATOR_NAME}**
            """)

# Footer
st.markdown(f"""
<div class="footer">
    <p>💖 Made with love by {CREATOR_NAME} | Powered by AI Magic ✨</p>
    <p>🍳 {BOT_NAME} - Your Kitchen Buddy & Timepass Companion 🍳</p>
</div>
""", unsafe_allow_html=True)
