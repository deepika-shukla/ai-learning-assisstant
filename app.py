"""
Streamlit Web Interface for AI Learning Assistant v2
Beautiful, interactive GUI with real-time updates.
"""

import streamlit as st
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

# Must be first Streamlit command
st.set_page_config(
    page_title="AI Learning Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment
load_dotenv()

# Import our modules
from state import create_initial_state
from graph import create_app


# ============================================================
# Session State Initialization
# ============================================================

def init_session():
    """Initialize Streamlit session state."""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())[:8]
    
    if "state" not in st.session_state:
        st.session_state.state = create_initial_state(
            user_id="streamlit_user",
            session_id=st.session_state.thread_id
        )
    
    if "app" not in st.session_state:
        st.session_state.app = create_app("streamlit_learning.db")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


# ============================================================
# Custom CSS
# ============================================================

def apply_custom_css():
    st.markdown("""
    <style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Chat messages */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 15px 15px 5px 15px;
        margin: 10px 0;
        max-width: 80%;
        margin-left: auto;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #2d3436 0%, #000000 100%);
        color: white;
        padding: 15px;
        border-radius: 15px 15px 15px 5px;
        margin: 10px 0;
        max-width: 80%;
        border-left: 4px solid #00cec9;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00b894, #00cec9);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #00cec9;
    }
    
    /* Quick action buttons */
    .quick-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        padding: 10px 20px;
        border-radius: 10px;
        color: white;
        margin: 5px;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .quick-btn:hover {
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# Sidebar Components
# ============================================================

def render_sidebar():
    """Render the sidebar with stats and controls."""
    with st.sidebar:
        st.markdown("# 🎓 Learning Dashboard")
        st.markdown("---")
        
        state = st.session_state.state
        
        # Topic display
        topic = state.get("topic", "")
        if topic:
            st.markdown(f"### 📚 {topic}")
        else:
            st.info("Start by telling me what you want to learn!")
        
        # Progress section
        if state.get("curriculum"):
            st.markdown("### 📊 Progress")
            
            curriculum = state["curriculum"]
            completed = state.get("completed_days", [])
            total = len(curriculum)
            progress = len(completed) / total if total > 0 else 0
            
            st.progress(progress)
            st.markdown(f"**Day {state.get('current_day', 1)} of {total}**")
            
            # Stats
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Completed", f"{len(completed)}/{total}")
            with col2:
                st.metric("Quizzes", state.get("quizzes_taken", 0))
            
            if state.get("average_quiz_score", 0) > 0:
                st.metric("Avg Score", f"{state['average_quiz_score']:.0f}%")
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Todos", use_container_width=True):
                process_quick_action("todos")
            if st.button("📝 Quiz", use_container_width=True):
                process_quick_action("quiz")
        with col2:
            if st.button("📊 Progress", use_container_width=True):
                process_quick_action("progress")
            if st.button("🌐 Resources", use_container_width=True):
                process_quick_action("resources")
        
        if st.button("✅ Mark Complete", use_container_width=True):
            process_quick_action("done")
        
        st.markdown("---")
        
        # Curriculum preview
        if state.get("curriculum") and state.get("curriculum_confirmed"):
            st.markdown("### 📅 Curriculum")
            current = state.get("current_day", 1)
            completed = state.get("completed_days", [])
            
            for day in state["curriculum"][:5]:  # Show first 5
                num = day["day_number"]
                if num in completed:
                    st.markdown(f"✅ ~~Day {num}: {day['title'][:25]}...~~")
                elif num == current:
                    st.markdown(f"📍 **Day {num}: {day['title'][:25]}...**")
                else:
                    st.markdown(f"⬜ Day {num}: {day['title'][:25]}...")
            
            if len(state["curriculum"]) > 5:
                st.markdown(f"*...and {len(state['curriculum'])-5} more days*")
        
        st.markdown("---")
        
        # Session info
        st.markdown("### 🔧 Session")
        st.code(f"ID: {st.session_state.thread_id}")
        
        if st.button("🔄 Reset Session", use_container_width=True):
            st.session_state.state = create_initial_state(
                user_id="streamlit_user",
                session_id=st.session_state.thread_id
            )
            st.session_state.chat_history = []
            st.rerun()


# ============================================================
# Chat Interface
# ============================================================

def process_message(user_input: str) -> str:
    """Process user message through the graph."""
    state = st.session_state.state
    app = st.session_state.app
    
    # Prepare input
    input_state = dict(state)
    input_state["messages"] = [HumanMessage(content=user_input)]
    
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    # Invoke graph
    result = app.invoke(input_state, config)
    
    # Update state
    st.session_state.state = result
    
    # Extract response
    messages = result.get("messages", [])
    if messages:
        last_msg = messages[-1]
        return last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    
    return "No response generated."


def process_quick_action(action: str):
    """Process a quick action button click."""
    response = process_message(action)
    st.session_state.chat_history.append(("user", action))
    st.session_state.chat_history.append(("assistant", response))
    st.rerun()


def render_chat():
    """Render the main chat interface."""
    st.markdown("## 💬 Chat")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for role, content in st.session_state.chat_history:
            if role == "user":
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(content)
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(content)
    
    # Chat input
    user_input = st.chat_input("Ask anything or type a command...")
    
    if user_input:
        # Add user message
        st.session_state.chat_history.append(("user", user_input))
        
        with st.spinner("Thinking..."):
            response = process_message(user_input)
        
        st.session_state.chat_history.append(("assistant", response))
        st.rerun()


# ============================================================
# Main Content
# ============================================================

def render_welcome():
    """Render welcome section for new users."""
    st.markdown("""
    <div style="text-align: center; padding: 40px;">
        <h1>🎓 Welcome to AI Learning Assistant</h1>
        <p style="font-size: 1.2em; color: #888;">
            Your personalized AI-powered learning companion
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📚 Learn Anything
        Tell me what you want to learn, and I'll create
        a personalized curriculum just for you.
        """)
    
    with col2:
        st.markdown("""
        ### 🌐 Rich Resources
        Get curated YouTube videos, Wikipedia summaries,
        and GitHub repositories for every topic.
        """)
    
    with col3:
        st.markdown("""
        ### 📝 Test Your Knowledge
        Take quizzes, track your progress, and earn
        achievements as you learn.
        """)
    
    st.markdown("---")
    
    st.markdown("### 🚀 Get Started")
    st.markdown("Try one of these:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🐍 Learn Python", use_container_width=True):
            process_quick_action("Teach me Python programming in 7 days")
    
    with col2:
        if st.button("⚛️ Learn React", use_container_width=True):
            process_quick_action("I want to learn React in 5 days")
    
    with col3:
        if st.button("🤖 Learn ML", use_container_width=True):
            process_quick_action("Teach me Machine Learning basics")


def render_resource_cards():
    """Render external resource cards if available."""
    state = st.session_state.state
    resources = state.get("content_recommendations")
    
    if resources:
        st.markdown("### 🌐 Learning Resources")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎬 Videos")
            for video in resources.get("youtube_videos", [])[:3]:
                st.markdown(f"- [{video['title'][:50]}...]({video['url']})")
        
        with col2:
            st.markdown("#### 💻 Repositories")
            for repo in resources.get("github_repos", [])[:3]:
                st.markdown(f"- [{repo['name']}]({repo['url']}) ⭐ {repo.get('stars', 0):,}")


# ============================================================
# Main App
# ============================================================

def main():
    """Main Streamlit application."""
    # Initialize
    init_session()
    apply_custom_css()
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OPENAI_API_KEY not found!")
        st.markdown("""
        Please create a `.env` file with:
        ```
        OPENAI_API_KEY=your_key_here
        ```
        """)
        return
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🎓 AI Learning Assistant v2")
        st.caption("Powered by LangGraph + OpenAI + External APIs")
    with col2:
        st.markdown(f"Session: `{st.session_state.thread_id}`")
    
    st.markdown("---")
    
    # Sidebar
    render_sidebar()
    
    # Main content
    if not st.session_state.chat_history:
        render_welcome()
    else:
        render_chat()
        
        # Show resources if available
        if st.session_state.state.get("content_recommendations"):
            with st.expander("🌐 Recent Resources", expanded=False):
                render_resource_cards()


if __name__ == "__main__":
    main()
