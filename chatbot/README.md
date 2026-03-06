# Personal Chatbot with Two Agents

A Python-based personal chatbot featuring two AI agents with distinct personalities and roles.

## Features

- **Two Distinct Agents**:
  - **Helper**: A friendly personal assistant for everyday questions and tasks
  - **Expert**: An analytical technical specialist for in-depth insights

- **Conversation Management**: Each agent maintains its own conversation history
- **Easy Switching**: Switch between agents during your conversation
- **Simple Interface**: Clean command-line interface

## Installation

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up OpenAI API Key** (for AI-powered version):
```bash
# Windows
set OPENAI_API_KEY=your-api-key-here

# Or create a .env file:
echo OPENAI_API_KEY=your-api-key-here > .env
```

## Usage

### Simple Version (Mock Responses)
Run the basic chatbot without API integration:
```bash
python chatbot.py
```

### OpenAI Version (Real AI Conversations)
Run the chatbot with OpenAI integration:
```bash
python chatbot_with_openai.py
```

### Available Commands

- `1` or `2` - Select an agent to chat with
- `switch` - Change to a different agent
- `clear` - Clear the current conversation history
- `agents` - List all available agents
- `quit` or `exit` - End the conversation

## Customization

### Adding New Agents

Create a new agent class in `chatbot.py`:

```python
class CustomAgent(Agent):
    def __init__(self):
        super().__init__(
            name="YourAgentName",
            role="Agent Role",
            personality="Personality description"
        )
    
    def get_system_prompt(self) -> str:
        return "Your custom system prompt here"
```

Then add it to the chatbot:

```python
class Chatbot:
    def __init__(self):
        self.agents = {
            "1": HelperAgent(),
            "2": ExpertAgent(),
            "3": CustomAgent()  # Add your new agent
        }
```

### Changing Agent Personalities

Modify the `get_system_prompt()` method in each agent class to change how they behave.

## Project Structure

```
chatbot/
├── chatbot.py              # Basic chatbot with mock responses
├── chatbot_with_openai.py  # OpenAI-integrated version
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Examples

### Example Conversation

```
Select an agent (1 or 2): 1

✓ Now chatting with Helper (Personal Assistant)
  I'm friendly, helpful, and always ready to assist with tasks and questions.

You: What's the weather like today?
Helper: I'd be happy to help! However, I don't have access to real-time weather data...

You: switch

Select an agent (1 or 2): 2

✓ Now chatting with Expert (Technical Specialist)
  I'm analytical, precise, and provide in-depth technical insights.

You: Explain how neural networks work
Expert: Neural networks are computational models inspired by biological neurons...
```

## Notes

- The basic version (`chatbot.py`) uses simulated responses
- The OpenAI version (`chatbot_with_openai.py`) requires an API key and makes actual AI calls
- Conversation history is maintained separately for each agent
- API costs apply when using the OpenAI version

## License

Free to use and modify for personal projects.
