"""
CLI Interface for AI Learning Assistant v2
Supports streaming, persistence, and rich output.
"""

import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

try:
    from .state import create_initial_state
    from .graph import create_app
except ImportError:
    from state import create_initial_state
    from graph import create_app

load_dotenv()


# ============================================================
# Rich Output Helpers
# ============================================================

def print_header():
    """Print application header."""
    header = """
╔══════════════════════════════════════════════════════════════════╗
║           🎓 AI LEARNING ASSISTANT v2.0                          ║
║   Powered by LangGraph + OpenAI + External APIs                  ║
╠══════════════════════════════════════════════════════════════════╣
║  Commands: todos, quiz, progress, resources, done, reset, help   ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(header)


def print_help():
    """Print help menu."""
    help_text = """
📚 AVAILABLE COMMANDS:
═══════════════════════════════════════════════════════════════════

📖 Learning:
  • "teach me [topic]"  - Start a new learning journey
  • "todos"             - See today's tasks
  • "resources"         - Get YouTube videos, Wikipedia, GitHub repos
  • "ask [question]"    - Ask anything about your topic

📝 Assessment:
  • "quiz"              - Take a knowledge check quiz
  • Answer with: "a, b, c, d, a" after quiz

📊 Progress:
  • "progress"          - View your learning progress
  • "analytics"         - Detailed statistics
  • "done"              - Mark current day complete

🔧 System:
  • "reset"             - Start fresh
  • "help"              - Show this menu
  • "exit" / "quit"     - Exit the application

═══════════════════════════════════════════════════════════════════
"""
    print(help_text)


def print_agent_indicator(agent_name: str):
    """Print which agent is responding."""
    agent_icons = {
        "router": "🔀",
        "curriculum": "📚",
        "confirm": "✅",
        "todos": "📋",
        "progress": "📊",
        "complete": "🎯",
        "qa": "💡",
        "quiz": "📝",
        "grader": "✍️",
        "resources": "🌐",
        "analytics": "📈",
        "unknown": "❓"
    }
    icon = agent_icons.get(agent_name, "🤖")
    print(f"\n{icon} [{agent_name.upper()}]")


# ============================================================
# Session Management
# ============================================================

class SessionManager:
    """Manages user sessions and state persistence."""
    
    def __init__(self, db_path: str = "learning_assistant.db"):
        self.db_path = db_path
        self.app = create_app(db_path)
        self.thread_id = None
        self.state = None
    
    def create_new_session(self) -> str:
        """Create a new session."""
        self.thread_id = str(uuid.uuid4())[:8]
        self.state = create_initial_state(
            user_id="cli_user",
            session_id=self.thread_id
        )
        print(f"🆕 New session started: {self.thread_id}")
        return self.thread_id
    
    def restore_session(self, thread_id: str) -> bool:
        """Try to restore an existing session."""
        self.thread_id = thread_id
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            checkpoint = self.app.get_state(config)
            if checkpoint and checkpoint.values:
                self.state = checkpoint.values
                topic = self.state.get("topic", "Unknown")
                day = self.state.get("current_day", 1)
                print(f"📂 Session restored: {thread_id}")
                print(f"   Topic: {topic}, Day: {day}")
                return True
        except Exception as e:
            print(f"Could not restore session: {e}")
        
        return False
    
    def get_config(self) -> dict:
        """Get config for graph invocation."""
        return {"configurable": {"thread_id": self.thread_id}}
    
    def process_message(self, user_input: str) -> str:
        """Process a user message and return the response."""
        # Add message to state
        if self.state is None:
            self.state = create_initial_state()
        
        # Create input with message
        input_state = dict(self.state)
        input_state["messages"] = [HumanMessage(content=user_input)]
        
        # Invoke graph
        config = self.get_config()
        result = self.app.invoke(input_state, config)
        
        # Update state from result
        self.state = result
        
        # Extract response
        messages = result.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "content"):
                return last_msg.content
            return str(last_msg)
        
        return "No response generated."
    
    def process_message_stream(self, user_input: str):
        """Process message with streaming output."""
        if self.state is None:
            self.state = create_initial_state()
        
        input_state = dict(self.state)
        input_state["messages"] = [HumanMessage(content=user_input)]
        
        config = self.get_config()
        
        # Stream through nodes
        for chunk in self.app.stream(input_state, config, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                if node_name != "router":
                    print_agent_indicator(node_name)
                    
                    # Extract and print message
                    messages = node_output.get("messages", [])
                    for msg in messages:
                        content = msg.content if hasattr(msg, "content") else str(msg)
                        print(content)
                
                # Update state
                self.state.update(node_output)
    
    def reset(self):
        """Reset to fresh state."""
        self.state = create_initial_state(
            user_id="cli_user",
            session_id=self.thread_id
        )
        print("🔄 Session reset. Start fresh by telling me what you want to learn!")


# ============================================================
# Main CLI Loop
# ============================================================

def main():
    """Main CLI entry point."""
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment.")
        print("Please create a .env file with: OPENAI_API_KEY=your_key_here")
        sys.exit(1)
    
    print_header()
    
    # Session setup
    session = SessionManager()
    
    # Check for existing session
    print("Would you like to:")
    print("  1. Start a new session")
    print("  2. Restore a previous session")
    
    choice = input("\nChoice (1/2) or session ID: ").strip()
    
    if choice == "2":
        session_id = input("Enter session ID: ").strip()
        if not session.restore_session(session_id):
            print("Session not found. Starting new session...")
            session.create_new_session()
    elif choice not in ["1", ""]:
        # Assume it's a session ID
        if not session.restore_session(choice):
            session.create_new_session()
    else:
        session.create_new_session()
    
    print("\n" + "="*60)
    print("💡 Tell me what you want to learn, or type 'help' for options")
    print("="*60 + "\n")
    
    # Main loop
    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle special commands
            lower_input = user_input.lower()
            
            if lower_input in ["exit", "quit", "bye", "q"]:
                print(f"\n👋 Goodbye! Your session ID is: {session.thread_id}")
                print("   Use this ID to restore your progress next time!")
                break
            
            if lower_input == "help":
                print_help()
                continue
            
            if lower_input == "reset":
                confirm = input("Are you sure? This will clear all progress (yes/no): ")
                if confirm.lower() in ["yes", "y"]:
                    session.reset()
                continue
            
            if lower_input == "session":
                print(f"📌 Current session: {session.thread_id}")
                if session.state:
                    print(f"   Topic: {session.state.get('topic', 'Not set')}")
                    print(f"   Day: {session.state.get('current_day', 1)}")
                continue
            
            # Process with streaming
            session.process_message_stream(user_input)
            
        except KeyboardInterrupt:
            print(f"\n\n👋 Session saved! ID: {session.thread_id}")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'help' for options.")


if __name__ == "__main__":
    main()
