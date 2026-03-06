"""
Personal Chatbot with Two Agents
This chatbot features two AI agents with different personalities and roles.
"""

import os
from typing import List, Dict
from abc import ABC, abstractmethod


class Agent(ABC):
    """Base class for chatbot agents"""
    
    def __init__(self, name: str, role: str, personality: str):
        self.name = name
        self.role = role
        self.personality = personality
        self.conversation_history: List[Dict[str, str]] = []
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
    
    def get_response(self, user_message: str) -> str:
        """Get response from the agent"""
        self.add_message("user", user_message)
        
        # Build the full conversation context
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ] + self.conversation_history
        
        # Simulate response (replace with actual LLM API call)
        response = self._generate_response(user_message)
        self.add_message("assistant", response)
        
        return response
    
    def _generate_response(self, user_message: str) -> str:
        """
        Generate a response. Override this method to integrate with actual LLM APIs.
        Currently returns a simulated response.
        """
        return f"[{self.name}]: I understand you said '{user_message}'. {self.personality}"
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []


class HelperAgent(Agent):
    """A helpful, friendly assistant agent"""
    
    def __init__(self):
        super().__init__(
            name="Helper",
            role="Personal Assistant",
            personality="I'm friendly, helpful, and always ready to assist with tasks and questions."
        )
    
    def get_system_prompt(self) -> str:
        return (
            "You are Helper, a friendly and supportive personal assistant. "
            "Your goal is to help users with their questions, provide useful information, "
            "and assist with various tasks. You are warm, encouraging, and patient. "
            "Always aim to be clear and helpful in your responses."
        )


class ExpertAgent(Agent):
    """An analytical, expert-level agent"""
    
    def __init__(self):
        super().__init__(
            name="Expert",
            role="Technical Specialist",
            personality="I'm analytical, precise, and provide in-depth technical insights."
        )
    
    def get_system_prompt(self) -> str:
        return (
            "You are Expert, a knowledgeable technical specialist. "
            "You provide detailed, accurate, and analytical responses. "
            "You excel at breaking down complex topics, providing expert insights, "
            "and giving thorough explanations. You are professional, precise, and comprehensive."
        )


class Chatbot:
    """Main chatbot class managing multiple agents"""
    
    def __init__(self):
        self.agents = {
            "1": HelperAgent(),
            "2": ExpertAgent()
        }
        self.current_agent = None
    
    def select_agent(self, choice: str) -> Agent:
        """Select an agent to chat with"""
        if choice in self.agents:
            self.current_agent = self.agents[choice]
            return self.current_agent
        return None
    
    def chat(self, message: str) -> str:
        """Send a message to the current agent"""
        if not self.current_agent:
            return "Please select an agent first."
        return self.current_agent.get_response(message)
    
    def list_agents(self) -> str:
        """List all available agents"""
        agent_list = []
        for key, agent in self.agents.items():
            agent_list.append(f"{key}. {agent.name} - {agent.role}")
        return "\n".join(agent_list)


def main():
    """Main function to run the chatbot"""
    chatbot = Chatbot()
    
    print("=" * 60)
    print("Welcome to Your Personal Chatbot!")
    print("=" * 60)
    print("\nAvailable Agents:")
    print(chatbot.list_agents())
    print("\nCommands:")
    print("  - Type 'switch' to change agents")
    print("  - Type 'clear' to clear conversation history")
    print("  - Type 'agents' to list available agents")
    print("  - Type 'quit' or 'exit' to end the conversation")
    print("=" * 60)
    
    while True:
        # Agent selection
        if not chatbot.current_agent:
            choice = input("\nSelect an agent (1 or 2): ").strip()
            agent = chatbot.select_agent(choice)
            if agent:
                print(f"\n✓ Now chatting with {agent.name} ({agent.role})")
                print(f"  {agent.personality}\n")
            else:
                print("Invalid choice. Please select 1 or 2.")
                continue
        
        # Get user input
        user_input = input(f"\nYou: ").strip()
        
        # Handle commands
        if user_input.lower() in ['quit', 'exit']:
            print("\nThank you for chatting! Goodbye! 👋")
            break
        elif user_input.lower() == 'switch':
            chatbot.current_agent = None
            print("\n" + "=" * 60)
            print(chatbot.list_agents())
            continue
        elif user_input.lower() == 'clear':
            if chatbot.current_agent:
                chatbot.current_agent.clear_history()
                print("✓ Conversation history cleared.")
            continue
        elif user_input.lower() == 'agents':
            print("\n" + chatbot.list_agents())
            continue
        elif not user_input:
            continue
        
        # Get and display response
        response = chatbot.chat(user_input)
        print(f"\n{chatbot.current_agent.name}: {response}")


if __name__ == "__main__":
    main()
