import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# Fix unicode error in Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

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

def get_response(client, history):
    messages = [{"role": "system", "content": MASTER_PROMPT}] + history
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        messages=messages,
    )
    return response.choices[0].message.content

def main():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable is not set.")
        return

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    history = []

    print("\n" + "💖" * 25)
    print("  😘 Welcome to RAJAN's Kitchen & Chat Corner! 😘")
    print("  ❤️‍🔥 Where food meets fun & love meets laughter ❤️‍🔥")
    print("💖" * 25 + "\n")
    user_name = input("  🌟 Enna da unoda peyar? (What's your name?) 👇 ").strip() or "friend"
    print("\n" + "💋" * 25 + "\n")

    opening = (
        f"The user's name is {user_name}. "
        f"Give a super fun, attractive, warm Tanglish welcome greeting using their name. "
        f"Introduce yourself as {BOT_NAME}, a funny cooking assistant and timepass buddy made by {CREATOR_NAME}. "
        f"Use lots of heart and kiss emojis 😘❤️💖🍳. Make it feel like a grand filmy entry. "
        f"Then invite them to ask anything about cooking or just chill and chat."
    )
    history.append({"role": "user", "content": opening})
    reply = get_response(client, history)
    history.append({"role": "assistant", "content": reply})
    print(f"\n{BOT_NAME}: {reply}\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            print(f"\n{BOT_NAME}: Ayyo {user_name}! Poitiya? 😭 Kitchen always open da! Come back soon! 😘❤️")
            break

        history.append({"role": "user", "content": user_input})
        reply = get_response(client, history)
        history.append({"role": "assistant", "content": reply})
        print(f"\n{BOT_NAME}: {reply}\n")

if __name__ == "__main__":
    main()
