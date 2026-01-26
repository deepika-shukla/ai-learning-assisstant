"""
AI Learning Assistant - Agent Definitions (v2)
12 specialized agents for comprehensive learning support.

INTERVIEW TIP: This module demonstrates "thinking indicators" - 
showing users what the AI is doing while processing their request.
This improves UX by providing transparency into AI reasoning.
"""

import os
import json
import asyncio
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Rich library for beautiful console output with thinking animations
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.panel import Panel
from rich.text import Text

try:
    from .state import LearningState, DayPlan, QuizQuestion, VALID_ACTIONS
    from .services.youtube_service import YouTubeService
    from .services.wikipedia_service import WikipediaService
    from .services.github_service import GitHubService
    from .services.web_search_service import WebSearchService
except ImportError:
    from state import LearningState, DayPlan, QuizQuestion, VALID_ACTIONS
    from services.youtube_service import YouTubeService
    from services.wikipedia_service import WikipediaService
    from services.github_service import GitHubService
    from services.web_search_service import WebSearchService

load_dotenv()

# Global console for thinking indicators
console = Console()


# ============================================================
# Thinking Indicator Utility
# ============================================================

class ThinkingIndicator:
    """
    Shows animated thinking process to users.
    
    INTERVIEW TIP: This provides transparency into AI reasoning,
    improving user trust and perceived responsiveness.
    """
    
    def __init__(self, initial_thought: str = "Processing..."):
        self.thoughts = []
        self.live = None
        self.initial_thought = initial_thought
    
    def __enter__(self):
        """Start the thinking display."""
        self.live = Live(
            self._render(),
            console=console,
            refresh_per_second=10,
            transient=True  # Disappears after completion
        )
        self.live.__enter__()
        return self
    
    def __exit__(self, *args):
        """Stop the thinking display."""
        if self.live:
            self.live.__exit__(*args)
    
    def think(self, thought: str):
        """Add a new thought to display."""
        self.thoughts.append(thought)
        if self.live:
            self.live.update(self._render())
        time.sleep(0.3)  # Brief pause for readability
    
    def _render(self):
        """Render current thoughts with spinner."""
        text = Text()
        text.append("🤔 ", style="bold yellow")
        text.append("AI is thinking...\n", style="bold cyan")
        
        for thought in self.thoughts:
            text.append(f"   💭 {thought}\n", style="dim")
        
        if not self.thoughts:
            text.append(f"   💭 {self.initial_thought}\n", style="dim")
        
        return Panel(text, border_style="cyan", padding=(0, 1))


def show_thinking(thoughts: list, final_action: str = None):
    """
    Display thinking process without Live context (simpler version).
    
    INTERVIEW TIP: This function shows step-by-step AI reasoning,
    making the system feel more intelligent and transparent.
    """
    console.print("\n🤔 [bold cyan]AI is thinking...[/bold cyan]")
    
    for thought in thoughts:
        time.sleep(0.2)
        console.print(f"   💭 [dim]{thought}[/dim]")
    
    if final_action:
        time.sleep(0.2)
        console.print(f"   ✅ [bold green]Action: {final_action}[/bold green]\n")


# ============================================================
# LLM Configuration
# ============================================================

def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    """Get configured LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY")
    )


# ============================================================
# Agent 1: Router Agent (NLP-based intent classification)
# ============================================================

def router_agent(state: LearningState) -> dict:
    """
    Central router that classifies user intent using LLM.
    Handles typos, variations, and natural language.
    
    INTERVIEW TIP: We use a two-tier approach:
    1. Quick keyword matching for common commands (fast, no API call)
    2. LLM classification for complex/ambiguous inputs (smart, uses API)
    """
    # Get last user message
    messages = state.get("messages", [])
    if not messages:
        return {"next_action": "unknown"}
    
    last_message = messages[-1]
    if hasattr(last_message, "content"):
        user_input = last_message.content
    else:
        user_input = str(last_message)
    
    user_lower = user_input.lower().strip()
    
    # ===== TIER 1: Quick keyword matching (no LLM needed) =====
    # INTERVIEW TIP: This saves API costs and reduces latency for common commands
    quick_match = {
        # Todos variations
        "todos": "show_todos",
        "todo": "show_todos",
        "tasks": "show_todos",
        "show todos": "show_todos",
        "show tasks": "show_todos",
        "my todos": "show_todos",
        "what to do": "show_todos",
        
        # Progress variations  
        "progress": "show_progress",
        "show progress": "show_progress",
        "my progress": "show_progress",
        "stats": "show_progress",
        
        # Quiz variations
        "quiz": "take_quiz",
        "quiz me": "take_quiz",
        "test me": "take_quiz",
        "take quiz": "take_quiz",
        
        # Resources variations
        "resources": "get_resources",
        "get resources": "get_resources",
        "videos": "get_resources",
        "tutorials": "get_resources",
        
        # Complete variations
        "done": "mark_complete",
        "complete": "mark_complete",
        "finished": "mark_complete",
        "mark done": "mark_complete",
        "mark complete": "mark_complete",
        
        # Analytics variations
        "analytics": "show_analytics",
        "show analytics": "show_analytics",
        "statistics": "show_analytics",
        
        # Confirm variations (YES)
        "yes": "confirm_curriculum",
        "confirm": "confirm_curriculum",
        "approve": "confirm_curriculum",
        "looks good": "confirm_curriculum",
        "let's start": "confirm_curriculum",
        "lets start": "confirm_curriculum",
        "ok": "confirm_curriculum",
        "okay": "confirm_curriculum",
        "sure": "confirm_curriculum",
        "sounds good": "confirm_curriculum",
        "perfect": "confirm_curriculum",
        "great": "confirm_curriculum",
        
        # Reject/Modify variations (NO) - Also routes to confirm agent
        "no": "confirm_curriculum",
        "nope": "confirm_curriculum",
        "change": "confirm_curriculum",
        "modify": "confirm_curriculum",
        "different": "confirm_curriculum",
        "not good": "confirm_curriculum",
        "don't like": "confirm_curriculum",
        "change it": "confirm_curriculum",
        "redo": "confirm_curriculum",
        "try again": "confirm_curriculum",
    }
    
    # Check for exact or partial match
    if user_lower in quick_match:
        # Show quick thinking for matched commands
        show_thinking(
            [f"Received: '{user_input}'", "Matched to quick command"],
            quick_match[user_lower]
        )
        return {"next_action": quick_match[user_lower]}
    
    # Check if input starts with a quick command
    for keyword, action in quick_match.items():
        if user_lower.startswith(keyword) or keyword.startswith(user_lower):
            show_thinking(
                [f"Received: '{user_input}'", f"Partial match: '{keyword}'"],
                action
            )
            return {"next_action": action}
    
    # ===== TIER 2: LLM classification for complex inputs =====
    # Show thinking for LLM classification
    show_thinking(
        [
            f"Received: '{user_input}'",
            "No quick match found",
            "Using LLM for intent classification...",
        ]
    )
    
    llm = get_llm(temperature=0)
    
    # Classification prompt
    system_prompt = """You are an intent classifier for an AI Learning Assistant.
Classify the user's message into EXACTLY ONE of these actions:

ACTIONS:
- create_curriculum: User wants to learn something new, start a course, create a plan
  Examples: "teach me Python", "I want to learn React", "start ML course"
  
- confirm_curriculum: User confirms/approves the proposed curriculum
  Examples: "yes", "looks good", "approve", "confirm", "let's start"
  
- show_todos: User wants to see today's tasks or what to do
  Examples: "show my tasks", "what should I do today", "my todos"
  
- mark_complete: User finished a topic/day and wants to mark it done
  Examples: "done with day 1", "completed", "finished today", "mark complete"
  
- show_progress: User wants to see their learning progress
  Examples: "show progress", "how am I doing", "my stats", "progress report"
  
- ask_question: User asks a question about their learning topic
  Examples: "what is a variable?", "explain OOP", "how does recursion work?"
  
- take_quiz: User wants to test their knowledge with a quiz
  Examples: "quiz me", "test my knowledge", "give me a quiz", "assess me"
  
- check_quiz: User is answering quiz questions (single letters a/b/c/d)
  Examples: "a", "b", "c", "d", "a,b,c", "my answers are a b c"
  
- get_resources: User wants external learning resources (videos, articles, repos)
  Examples: "get resources", "find videos", "show tutorials", "github repos"
  
- show_analytics: User wants to see their learning analytics
  Examples: "my analytics", "show statistics", "how much time spent"
  
- unknown: Message doesn't match any action

IMPORTANT:
- If unsure, prefer "ask_question" for any learning-related question
- Handle typos gracefully (e.g., "progrss" → show_progress)
- Respond with ONLY the action name, nothing else"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Classify this message: {user_input}")
    ])
    
    # Extract and validate action
    action = response.content.strip().lower().replace('"', '').replace("'", "")
    
    # Clean common LLM artifacts
    for prefix in ["action:", "intent:", "the action is", "classified as"]:
        if action.startswith(prefix):
            action = action[len(prefix):].strip()
    
    # Validate action
    if action not in VALID_ACTIONS:
        # Try fuzzy matching
        for valid in VALID_ACTIONS:
            if valid in action or action in valid:
                action = valid
                break
        else:
            action = "unknown"
    
    # Show final classification
    console.print(f"   ✅ [bold green]Classified as: {action}[/bold green]\n")
    
    return {"next_action": action}


# ============================================================
# Agent 2: Curriculum Agent (Generates learning plans)
# ============================================================

def curriculum_agent(state: LearningState) -> dict:
    """
    Creates a personalized multi-day learning curriculum.
    Considers skill level and duration.
    
    INTERVIEW TIP: We extract duration from natural language using regex.
    "teach me Python for 3 days" → duration = 3
    """
    import re
    
    llm = get_llm(temperature=0.8)
    
    # Extract topic from message if not in state
    topic = state.get("topic", "")
    messages = state.get("messages", [])
    user_message = ""
    
    if messages:
        last_msg = messages[-1]
        user_message = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        if not topic:
            topic = user_message
    
    # Extract duration from user message (e.g., "3 days", "5 day", "in 10 days")
    duration = state.get("duration_days", 7)  # Default to 7
    
    # INTERVIEW TIP: Regex pattern to find "N days" or "N day" in message
    duration_match = re.search(r'(\d+)\s*(?:days?|day)', user_message.lower())
    if duration_match:
        extracted_duration = int(duration_match.group(1))
        # Sanity check: keep between 1-30 days
        if 1 <= extracted_duration <= 30:
            duration = extracted_duration
    
    # Show thinking process
    show_thinking([
        f"User wants to learn: {topic}",
        f"Duration requested: {duration} days",
        f"Skill level: {state.get('skill_level', 'beginner')}",
        "Generating personalized curriculum...",
    ])
    
    level = state.get("skill_level", "beginner")
    
    system_prompt = f"""You are an expert curriculum designer. Create a {duration}-day learning plan.

REQUIREMENTS:
1. Topic: {topic}
2. Duration: {duration} days
3. Skill Level: {level}

OUTPUT FORMAT (valid JSON array):
[
  {{"day_number": 1, "title": "Day 1: Introduction", "topics": ["topic1", "topic2"], "completed": false}},
  {{"day_number": 2, "title": "Day 2: Fundamentals", "topics": ["topic3", "topic4"], "completed": false}}
]

RULES:
- Each day should have 2-4 specific topics
- Progress from basics to advanced
- Make titles descriptive and engaging
- Topics should be actionable learning objectives
- Return ONLY the JSON array, no other text"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Create a {duration}-day curriculum for learning: {topic}")
    ])
    
    # Parse JSON from response
    try:
        content = response.content.strip()
        # Clean potential markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        curriculum = json.loads(content)
        
        # Ensure proper structure
        for day in curriculum:
            day["completed"] = False
            if "day_number" not in day:
                day["day_number"] = curriculum.index(day) + 1
                
    except (json.JSONDecodeError, Exception) as e:
        print(f"Curriculum parse error: {e}")
        # Fallback curriculum
        curriculum = [
            {"day_number": i, "title": f"Day {i}: Learning {topic}", 
             "topics": [f"{topic} concept {i}"], "completed": False}
            for i in range(1, duration + 1)
        ]
    
    # Create confirmation message
    curriculum_text = "\n".join([
        f"📅 **{day['title']}**\n   • " + "\n   • ".join(day['topics'])
        for day in curriculum
    ])
    
    confirmation_msg = f"""📚 **Here's your personalized {duration}-day curriculum for {topic}:**

{curriculum_text}

---
✅ Type **'yes'** or **'confirm'** to start learning!
❌ Type **'no'** or describe changes you'd like."""

    return {
        "curriculum": curriculum,
        "topic": topic,
        "messages": [AIMessage(content=confirmation_msg)],
        "next_action": "confirm_curriculum"
    }


# ============================================================
# Agent 3: Confirm Curriculum Agent (Human-in-the-loop)
# ============================================================

def confirm_curriculum_agent(state: LearningState) -> dict:
    """
    Handles curriculum confirmation (human-in-the-loop gate).
    """
    messages = state.get("messages", [])
    curriculum = state.get("curriculum", [])
    
    if not messages:
        return {"curriculum_confirmed": False}
    
    last_msg = messages[-1]
    content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    response_lower = content.lower().strip()
    
    # Check for positive confirmation
    positive_keywords = ["yes", "confirm", "approve", "ok", "okay", "sure", 
                        "sounds good", "let's go", "start", "begin", "perfect",
                        "looks good", "great", "love it", "👍"]
    
    if any(kw in response_lower for kw in positive_keywords):
        if curriculum:
            first_day = curriculum[0]
            topics = ", ".join(first_day.get("topics", []))
            
            return {
                "curriculum_confirmed": True,
                "current_day": 1,
                "messages": [AIMessage(content=f"""🎉 **Excellent! Your learning journey begins!**

📅 **{first_day['title']}**
📝 Today's Topics: {topics}

**What you can do:**
• `"todos"` - See today's detailed tasks
• `"resources"` - Get videos, articles & repos
• `"quiz"` - Test your knowledge
• `"ask [question]"` - Ask any question
• `"done"` - Mark today complete

Let's start learning! 🚀""")]
            }
    
    # Negative or modification request
    return {
        "curriculum_confirmed": False,
        "messages": [AIMessage(content="""I understand you'd like changes. Please tell me:

1. What would you like to modify?
2. Should I add/remove any topics?
3. Different duration or pace?

Just describe what you'd like, and I'll regenerate the curriculum!""")]
    }


# ============================================================
# Agent 4: Todo Agent (Daily task breakdown)
# ============================================================

def todo_agent(state: LearningState) -> dict:
    """
    Generates detailed tasks for the current day.
    """
    llm = get_llm(temperature=0.7)
    
    curriculum = state.get("curriculum", [])
    current_day = state.get("current_day", 1)
    topic = state.get("topic", "the subject")
    level = state.get("skill_level", "beginner")
    
    if not curriculum:
        return {
            "todos": [],
            "messages": [AIMessage(content="📚 No curriculum yet! Tell me what you want to learn.")]
        }
    
    # Find current day
    current_day_plan = None
    for day in curriculum:
        if day.get("day_number") == current_day:
            current_day_plan = day
            break
    
    if not current_day_plan:
        return {
            "messages": [AIMessage(content=f"🎉 You've completed all {len(curriculum)} days! Congratulations!")]
        }
    
    topics = current_day_plan.get("topics", [])
    
    # Show thinking process
    show_thinking([
        f"Fetching tasks for Day {current_day}",
        f"Today's focus: {current_day_plan['title']}",
        f"Topics: {', '.join(topics[:3])}{'...' if len(topics) > 3 else ''}",
        "Generating actionable tasks...",
    ])
    
    system_prompt = f"""Generate a detailed task list for a {level} learner.
Topic: {topic}
Day: {current_day}
Today's focus: {current_day_plan['title']}
Topics to cover: {', '.join(topics)}

Create 5-7 specific, actionable tasks. Format each as:
□ Task description (15 min) - brief explanation

Make tasks progressive and include:
- Reading/watching content
- Hands-on practice
- Small projects or exercises
- Review/reflection"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="Generate today's learning tasks")
    ])
    
    # Parse tasks
    tasks = []
    for line in response.content.split("\n"):
        line = line.strip()
        if line and (line.startswith("□") or line.startswith("-") or 
                    line.startswith("•") or (line[0].isdigit() and "." in line)):
            # Clean the line
            clean = line.lstrip("□-•0123456789.").strip()
            if clean:
                tasks.append(f"□ {clean}")
    
    if not tasks:
        tasks = [f"□ Study: {t}" for t in topics]
    
    task_text = "\n".join(tasks)
    
    return {
        "todos": tasks,
        "messages": [AIMessage(content=f"""📋 **{current_day_plan['title']}**

**Today's Tasks:**
{task_text}

---
💡 **Tips:**
• `"resources"` - Get videos & articles for these topics
• `"ask [question]"` - Ask anything you don't understand
• `"done"` - Mark day complete when finished""")]
    }


# ============================================================
# Agent 5: Progress Agent (Learning analytics)
# ============================================================

def progress_agent(state: LearningState) -> dict:
    """
    Shows comprehensive learning progress and statistics.
    """
    curriculum = state.get("curriculum", [])
    completed_days = state.get("completed_days", [])
    current_day = state.get("current_day", 1)
    topic = state.get("topic", "your subject")
    quizzes_taken = state.get("quizzes_taken", 0)
    avg_score = state.get("average_quiz_score", 0.0)
    questions_asked = state.get("questions_asked", 0)
    
    if not curriculum:
        return {
            "messages": [AIMessage(content="📊 No curriculum yet! Start by telling me what you want to learn.")]
        }
    
    total_days = len(curriculum)
    completed_count = len(completed_days)
    progress_percent = (completed_count / total_days) * 100 if total_days > 0 else 0
    
    # Progress bar
    filled = int(progress_percent / 5)
    bar = "█" * filled + "░" * (20 - filled)
    
    # Day status
    day_status = []
    for day in curriculum:
        num = day["day_number"]
        if num in completed_days:
            status = "✅"
        elif num == current_day:
            status = "📍"
        else:
            status = "⬜"
        day_status.append(f"{status} Day {num}: {day['title']}")
    
    status_text = "\n".join(day_status)
    
    # Achievements
    achievements = []
    if completed_count >= 1:
        achievements.append("🏆 First Day Complete")
    if completed_count >= 3:
        achievements.append("🔥 3-Day Streak")
    if completed_count >= 7:
        achievements.append("⭐ Week Warrior")
    if quizzes_taken >= 1:
        achievements.append("📝 Quiz Taker")
    if avg_score >= 80:
        achievements.append("🎯 Quiz Master")
    if questions_asked >= 5:
        achievements.append("❓ Curious Mind")
    if completed_count == total_days:
        achievements.append("🎓 Course Complete!")
    
    achievements_text = "\n".join(achievements) if achievements else "Keep learning to earn achievements!"
    
    return {
        "messages": [AIMessage(content=f"""📊 **Learning Progress: {topic}**

**Progress: {progress_percent:.0f}%**
[{bar}] {completed_count}/{total_days} days

---
**📅 Daily Progress:**
{status_text}

---
**📈 Statistics:**
• Quizzes Taken: {quizzes_taken}
• Average Score: {avg_score:.0f}%
• Questions Asked: {questions_asked}
• Current Day: {current_day}

---
**🏅 Achievements:**
{achievements_text}""")]
    }


# ============================================================
# Agent 6: Complete Day Agent
# ============================================================

def complete_day_agent(state: LearningState) -> dict:
    """
    Marks the current day as complete and advances.
    """
    curriculum = state.get("curriculum", [])
    current_day = state.get("current_day", 1)
    completed_days = list(state.get("completed_days", []))
    
    if not curriculum:
        return {
            "messages": [AIMessage(content="📚 No curriculum to complete! Start by creating one.")]
        }
    
    # Mark current day complete
    if current_day not in completed_days:
        completed_days.append(current_day)
    
    # Update curriculum
    updated_curriculum = []
    for day in curriculum:
        day_copy = dict(day)
        if day_copy["day_number"] == current_day:
            day_copy["completed"] = True
        updated_curriculum.append(day_copy)
    
    total_days = len(curriculum)
    next_day = current_day + 1
    
    if next_day > total_days:
        # Course complete!
        return {
            "completed_days": completed_days,
            "curriculum": updated_curriculum,
            "messages": [AIMessage(content=f"""🎓 **CONGRATULATIONS!!!**

You've completed your entire {total_days}-day curriculum! 

🏆 **Achievement Unlocked:** Course Complete!

**What's Next?**
• Take a final comprehensive quiz
• Review any topics you want to reinforce
• Start a new learning journey!

You did amazing! 🌟""")]
        }
    
    # Find next day info
    next_day_plan = None
    for day in curriculum:
        if day["day_number"] == next_day:
            next_day_plan = day
            break
    
    if next_day_plan:
        topics = ", ".join(next_day_plan.get("topics", []))
        
        return {
            "completed_days": completed_days,
            "current_day": next_day,
            "curriculum": updated_curriculum,
            "todos": [],
            "messages": [AIMessage(content=f"""✅ **Day {current_day} Complete!**

Great progress! You've finished {len(completed_days)}/{total_days} days.

---
📅 **Up Next: {next_day_plan['title']}**
📝 Topics: {topics}

**Commands:**
• `"todos"` - See Day {next_day}'s tasks
• `"resources"` - Get learning materials
• `"quiz"` - Test what you learned today

Keep up the great work! 🚀""")]
        }
    
    return {
        "completed_days": completed_days,
        "current_day": next_day,
        "curriculum": updated_curriculum
    }


# ============================================================
# Agent 7: Q&A Agent (Answers learning questions)
# ============================================================

def qa_agent(state: LearningState) -> dict:
    """
    Answers questions about the learning topic.
    Context-aware based on current curriculum.
    """
    llm = get_llm(temperature=0.7)
    
    messages = state.get("messages", [])
    topic = state.get("topic", "general programming")
    level = state.get("skill_level", "beginner")
    curriculum = state.get("curriculum", [])
    current_day = state.get("current_day", 1)
    questions_asked = state.get("questions_asked", 0)
    
    if not messages:
        return {"messages": [AIMessage(content="What would you like to know?")]}
    
    last_msg = messages[-1]
    question = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    
    # Get current day context
    current_topics = []
    if curriculum:
        for day in curriculum:
            if day["day_number"] == current_day:
                current_topics = day.get("topics", [])
                break
    
    context = f"Currently learning: {', '.join(current_topics)}" if current_topics else ""
    
    system_prompt = f"""You are a helpful programming tutor teaching {topic} to a {level} learner.

{context}

GUIDELINES:
1. Explain concepts clearly with examples
2. Use analogies for complex topics
3. Provide code examples when relevant (use markdown code blocks)
4. Keep explanations appropriate for {level} level
5. Be encouraging and supportive
6. If the question is unclear, ask for clarification

Format your response with:
- Clear headers if needed
- Code blocks with syntax highlighting
- Bullet points for lists"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=question)
    ])
    
    return {
        "questions_asked": questions_asked + 1,
        "messages": [AIMessage(content=response.content)]
    }


# ============================================================
# Agent 8: Quiz Agent (Generates quizzes)
# ============================================================

def quiz_agent(state: LearningState) -> dict:
    """
    Generates topic-specific quiz questions.
    """
    llm = get_llm(temperature=0.8)
    
    curriculum = state.get("curriculum", [])
    current_day = state.get("current_day", 1)
    topic = state.get("topic", "programming")
    level = state.get("skill_level", "beginner")
    
    # Get topics to quiz on
    quiz_topics = []
    if curriculum:
        for day in curriculum:
            if day["day_number"] <= current_day:
                quiz_topics.extend(day.get("topics", []))
    
    if not quiz_topics:
        quiz_topics = [topic]
    
    # Show thinking process
    show_thinking([
        f"Preparing quiz for Day {current_day}",
        f"Skill level: {level}",
        f"Topics covered: {', '.join(quiz_topics[-3:])}",
        "Generating challenging questions...",
    ])
    
    system_prompt = f"""Create a 5-question multiple choice quiz for a {level} learner.

Topics: {', '.join(quiz_topics[-6:])}  # Last 6 topics for relevance

OUTPUT FORMAT (valid JSON array):
[
  {{
    "question": "What is...?",
    "options": ["a) Option 1", "b) Option 2", "c) Option 3", "d) Option 4"],
    "correct_answer": "a",
    "explanation": "Because..."
  }}
]

RULES:
- 5 questions total
- Mix of difficulty levels
- One clearly correct answer per question
- Explanations should teach, not just state the answer
- Return ONLY valid JSON"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Create a quiz about: {', '.join(quiz_topics[-4:])}")
    ])
    
    # Parse quiz
    try:
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        questions = json.loads(content)
    except Exception as e:
        print(f"Quiz parse error: {e}")
        # Fallback question
        questions = [{
            "question": f"What is an important concept in {topic}?",
            "options": ["a) Concept A", "b) Concept B", "c) Concept C", "d) Concept D"],
            "correct_answer": "a",
            "explanation": "This is a fundamental concept."
        }]
    
    # Format quiz display
    quiz_text = "📝 **Knowledge Check Quiz**\n\n"
    for i, q in enumerate(questions, 1):
        quiz_text += f"**Question {i}:** {q['question']}\n"
        for opt in q.get("options", []):
            quiz_text += f"   {opt}\n"
        quiz_text += "\n"
    
    quiz_text += "---\n✍️ **Reply with your answers** (e.g., `a, b, c, d, a`)"
    
    return {
        "quiz_questions": questions,
        "user_answers": [],
        "messages": [AIMessage(content=quiz_text)]
    }


# ============================================================
# Agent 9: Quiz Grader Agent
# ============================================================

def quiz_grader_agent(state: LearningState) -> dict:
    """
    Grades quiz answers and provides feedback.
    """
    messages = state.get("messages", [])
    questions = state.get("quiz_questions", [])
    quizzes_taken = state.get("quizzes_taken", 0)
    avg_score = state.get("average_quiz_score", 0.0)
    
    if not questions:
        return {
            "messages": [AIMessage(content="📝 No active quiz. Type `quiz` to start one!")]
        }
    
    if not messages:
        return {
            "messages": [AIMessage(content="Please provide your answers (e.g., `a, b, c, d, a`)")]
        }
    
    # Parse user answers
    last_msg = messages[-1]
    answer_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    
    # Extract letters
    import re
    answers = re.findall(r'[a-dA-D]', answer_text.lower())
    
    if len(answers) < len(questions):
        return {
            "messages": [AIMessage(content=f"I found {len(answers)} answers but there are {len(questions)} questions. Please provide all answers (e.g., `a, b, c, d, a`)")]
        }
    
    # Grade
    correct = 0
    feedback = "📊 **Quiz Results**\n\n"
    
    for i, q in enumerate(questions):
        user_ans = answers[i] if i < len(answers) else "?"
        correct_ans = q.get("correct_answer", "a").lower()
        
        if user_ans == correct_ans:
            correct += 1
            feedback += f"✅ **Q{i+1}:** Correct!\n"
        else:
            feedback += f"❌ **Q{i+1}:** Your answer: {user_ans}, Correct: {correct_ans}\n"
            feedback += f"   💡 {q.get('explanation', 'Review this topic.')}\n"
        feedback += "\n"
    
    score = (correct / len(questions)) * 100 if questions else 0
    
    # Update average
    new_quizzes = quizzes_taken + 1
    new_avg = ((avg_score * quizzes_taken) + score) / new_quizzes
    
    # Score message
    if score == 100:
        grade_msg = "🌟 **PERFECT SCORE!** You've mastered this material!"
    elif score >= 80:
        grade_msg = "🎉 **Great job!** You have a solid understanding!"
    elif score >= 60:
        grade_msg = "👍 **Good effort!** Review the topics you missed."
    else:
        grade_msg = "📚 **Keep studying!** Review the explanations above."
    
    feedback += f"---\n**Score: {correct}/{len(questions)} ({score:.0f}%)**\n{grade_msg}"
    
    return {
        "quiz_score": int(score),
        "user_answers": answers[:len(questions)],
        "quizzes_taken": new_quizzes,
        "average_quiz_score": new_avg,
        "quiz_questions": [],  # Clear for next quiz
        "messages": [AIMessage(content=feedback)]
    }


# ============================================================
# Agent 10: Resources Agent (NEW - External APIs!)
# ============================================================

def resources_agent(state: LearningState) -> dict:
    """
    Fetches external learning resources using APIs.
    Integrates YouTube, Wikipedia, and GitHub.
    Can fetch specific resources or all based on user request.
    """
    curriculum = state.get("curriculum", [])
    current_day = state.get("current_day", 1)
    topic = state.get("topic", "programming")
    messages = state.get("messages", [])
    
    # Detect which specific resource user wants
    last_msg = messages[-1].content.lower() if messages else ""
    
    want_youtube = any(word in last_msg for word in ["youtube", "video", "videos", "watch"])
    want_wikipedia = any(word in last_msg for word in ["wikipedia", "wiki", "summary", "what is", "explain"])
    want_github = any(word in last_msg for word in ["github", "repo", "repos", "repository", "code", "project"])
    want_web = any(word in last_msg for word in ["search", "web", "google", "find", "look up", "articles"])
    
    # If none specified or user says "resources", get all
    want_all = "resources" in last_msg or (not want_youtube and not want_wikipedia and not want_github and not want_web)
    
    # Try to extract topic from user's last message
    user_topic = None
    if messages:
        # Extract topic from messages like "Find YouTube videos on Python"
        for keyword in ["on ", "for ", "about ", "learn "]:
            if keyword in last_msg:
                user_topic = last_msg.split(keyword)[-1].strip().rstrip("?!.")
                break
    
    # Get current topics from curriculum
    current_topics = []
    if curriculum:
        for day in curriculum:
            if day["day_number"] == current_day:
                current_topics = day.get("topics", [])
                break
    
    # Priority: user's explicit topic > curriculum topics > state topic
    if user_topic and len(user_topic) > 1:
        search_query = user_topic
        display_topic = user_topic.title()
    elif current_topics:
        search_query = " ".join(current_topics[:2])
        display_topic = ", ".join(current_topics)
    else:
        search_query = topic
        display_topic = topic.title() if topic else "Programming"
    
    # Show thinking process
    thinking_items = [f"Searching for: {display_topic}"]
    if want_all:
        thinking_items.extend(["Fetching YouTube videos...", "Searching Wikipedia...", "Finding GitHub repos..."])
    else:
        if want_youtube:
            thinking_items.append("Fetching YouTube videos...")
        if want_wikipedia:
            thinking_items.append("Searching Wikipedia...")
        if want_github:
            thinking_items.append("Finding GitHub repos...")
        if want_web:
            thinking_items.append("Searching the web...")
    
    show_thinking(thinking_items)
    
    # Fetch from services based on what user wants
    youtube = YouTubeService()
    wikipedia = WikipediaService()
    github = GitHubService()
    web_search = WebSearchService()
    
    # Improve Wikipedia search by adding context for ambiguous terms
    wiki_query = search_query
    tech_terms = {
        "python": "Python programming language",
        "java": "Java programming language", 
        "rust": "Rust programming language",
        "go": "Go programming language",
        "ruby": "Ruby programming language",
        "swift": "Swift programming language",
        "docker": "Docker software",
        "kubernetes": "Kubernetes",
        "react": "React JavaScript library",
        "node": "Node.js",
        "angular": "Angular framework",
        "vue": "Vue.js",
    }
    if search_query.lower() in tech_terms:
        wiki_query = tech_terms[search_query.lower()]
    
    videos = []
    wiki = {"summary": "", "url": ""}
    repos = []
    web_results = []
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Only fetch what user asked for
        if want_youtube or want_all:
            videos = loop.run_until_complete(youtube.search_videos(search_query + " tutorial", max_results=3))
        if want_wikipedia or want_all:
            wiki = loop.run_until_complete(wikipedia.get_summary(wiki_query))
        if want_github or want_all:
            repos = loop.run_until_complete(github.search_repositories(search_query + " tutorial", max_results=3))
        
        loop.close()
        
        # Web search (synchronous)
        if want_web or want_all:
            web_results = web_search.search(f"{search_query} tutorial guide", max_results=3)
            
    except Exception as e:
        print(f"Resource fetch error: {e}")
    
    # Format response based on what was requested
    response = f"📚 **Learning Resources for {display_topic}**\n\n---\n"
    
    # YouTube section
    if want_youtube or want_all:
        response += "\n🎬 **YouTube Videos:**\n"
        for v in videos[:3]:
            response += f"• [{v['title'][:50]}...]({v['url']})\n"
            response += f"  _{v.get('channel', 'Unknown channel')}_\n"
        if not videos:
            response += f"• [Search YouTube for: {display_topic}](https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}+tutorial)\n"
        response += "\n---\n"
    
    # Wikipedia section
    if want_wikipedia or want_all:
        wiki_summary = wiki.get('summary', 'No summary available')[:300]
        wiki_url = wiki.get('url', 'https://wikipedia.org')
        response += f"\n📖 **Wikipedia Summary:**\n{wiki_summary}...\n\n🔗 [Read more on Wikipedia]({wiki_url})\n\n---\n"
    
    # Web Search section (NEW!)
    if want_web or want_all:
        response += "\n🔍 **Web Search Results:**\n"
        for r in web_results[:3]:
            title = r.get('title', 'No title')[:50]
            snippet = r.get('snippet', '')[:100]
            url = r.get('url', '')
            response += f"• **{title}**\n"
            response += f"  {snippet}...\n"
            response += f"  🔗 {url}\n\n"
        if not web_results:
            response += "• No web results found. Try: `search for [topic]`\n"
        response += "---\n"
    
    # GitHub section
    if want_github or want_all:
        response += "\n💻 **GitHub Repositories:**\n"
        for r in repos[:3]:
            response += f"• [{r['name']}]({r['url']}) ⭐ {r.get('stars', 0):,}\n"
            response += f"  _{r.get('description', 'No description')[:60]}_\n"
        if not repos:
            response += "• No repositories found.\n"
        response += "\n---\n"
    
    response += "💡 **Tip:** These resources complement your curriculum!"

    # Store recommendations
    recommendations = {
        "youtube_videos": videos,
        "wikipedia_summary": wiki.get("summary", ""),
        "github_repos": repos
    }
    
    return {
        "content_recommendations": recommendations,
        "messages": [AIMessage(content=response)]
    }


# ============================================================
# Agent 11: Analytics Agent (NEW!)
# ============================================================

def analytics_agent(state: LearningState) -> dict:
    """
    Shows detailed learning analytics.
    """
    completed_days = state.get("completed_days", [])
    quizzes_taken = state.get("quizzes_taken", 0)
    avg_score = state.get("average_quiz_score", 0.0)
    questions_asked = state.get("questions_asked", 0)
    curriculum = state.get("curriculum", [])
    topic = state.get("topic", "Unknown")
    
    total_days = len(curriculum)
    completion_rate = (len(completed_days) / total_days * 100) if total_days > 0 else 0
    
    # Estimate time spent (rough)
    estimated_hours = len(completed_days) * 1.5  # Assume 1.5 hours per day
    
    response = f"""📈 **Your Learning Analytics**

**Course:** {topic}
**Duration:** {total_days} days

---

**📊 Progress Metrics:**
┌─────────────────────┬──────────┐
│ Days Completed      │ {len(completed_days):>7} │
│ Completion Rate     │ {completion_rate:>6.0f}% │
│ Estimated Hours     │ {estimated_hours:>6.1f}h │
└─────────────────────┴──────────┘

**📝 Quiz Performance:**
┌─────────────────────┬──────────┐
│ Quizzes Taken       │ {quizzes_taken:>7} │
│ Average Score       │ {avg_score:>6.0f}% │
│ Questions Asked     │ {questions_asked:>7} │
└─────────────────────┴──────────┘

**🎯 Learning Style Insights:**
"""
    
    if questions_asked > quizzes_taken * 2:
        response += "• You're a **curious learner** - great at asking questions!\n"
    if quizzes_taken > len(completed_days):
        response += "• You're **assessment-focused** - love testing your knowledge!\n"
    if avg_score >= 80:
        response += "• You're a **high performer** - excellent retention!\n"
    elif quizzes_taken == 0:
        response += "• **Tip:** Try taking quizzes to test your knowledge!\n"
    
    response += """
---
Keep learning! Every day brings you closer to mastery. 🚀"""
    
    return {
        "messages": [AIMessage(content=response)]
    }


# ============================================================
# Agent 12: Unknown Agent (Fallback)
# ============================================================

def unknown_agent(state: LearningState) -> dict:
    """
    Handles unrecognized inputs gracefully.
    """
    curriculum_exists = bool(state.get("curriculum"))
    confirmed = state.get("curriculum_confirmed", False)
    
    if not curriculum_exists:
        help_text = """🤔 I'm not sure what you mean.

**To get started, tell me what you want to learn!**
Examples:
• "Teach me Python"
• "I want to learn React"
• "Start a machine learning course"
"""
    elif not confirmed:
        help_text = """🤔 I didn't understand that.

**Your curriculum is waiting for confirmation!**
• Type `yes` to confirm and start learning
• Or describe any changes you'd like
"""
    else:
        help_text = """🤔 I'm not sure what you mean. Here are available commands:

**📚 Learning:**
• `todos` - See today's tasks
• `resources` - Get videos, articles & repos
• `quiz` - Test your knowledge
• `ask [question]` - Ask anything

**📊 Progress:**
• `progress` - View your progress
• `analytics` - Detailed statistics
• `done` - Mark day complete

**🔧 Other:**
• `reset` - Start over
• `help` - Show this menu
"""
    
    return {
        "messages": [AIMessage(content=help_text)]
    }
