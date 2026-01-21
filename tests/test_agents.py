"""
Unit tests for agent functions.
"""

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage


class TestRouterAgent:
    """Tests for the router agent."""
    
    def test_router_with_empty_messages(self, empty_state):
        """Router should return 'unknown' for empty messages."""
        from agents import router_agent
        
        with patch("agents.get_llm") as mock_llm:
            result = router_agent(empty_state)
            assert result["next_action"] == "unknown"
    
    def test_router_classifies_curriculum_request(self, empty_state, mock_openai):
        """Router should classify 'teach me Python' as create_curriculum."""
        from agents import router_agent
        
        empty_state["messages"] = [HumanMessage(content="teach me Python")]
        
        with patch("agents.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(content="create_curriculum")
            mock_get_llm.return_value = mock_llm
            
            result = router_agent(empty_state)
            assert result["next_action"] == "create_curriculum"
    
    def test_router_classifies_quiz_request(self, state_with_curriculum):
        """Router should classify 'quiz me' as take_quiz."""
        from agents import router_agent
        
        state_with_curriculum["messages"] = [HumanMessage(content="quiz me")]
        
        with patch("agents.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(content="take_quiz")
            mock_get_llm.return_value = mock_llm
            
            result = router_agent(state_with_curriculum)
            assert result["next_action"] == "take_quiz"
    
    def test_router_handles_typos(self, state_with_curriculum):
        """Router should handle typos via LLM classification."""
        from agents import router_agent
        
        state_with_curriculum["messages"] = [HumanMessage(content="shwo progrss")]
        
        with patch("agents.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(content="show_progress")
            mock_get_llm.return_value = mock_llm
            
            result = router_agent(state_with_curriculum)
            assert result["next_action"] == "show_progress"


class TestCurriculumAgent:
    """Tests for the curriculum agent."""
    
    def test_curriculum_generates_plan(self, empty_state):
        """Curriculum agent should generate a learning plan."""
        from agents import curriculum_agent
        
        empty_state["topic"] = "Python"
        empty_state["duration_days"] = 3
        
        with patch("agents.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(
                content='[{"day_number": 1, "title": "Day 1", "topics": ["Intro"], "completed": false}]'
            )
            mock_get_llm.return_value = mock_llm
            
            result = curriculum_agent(empty_state)
            
            assert "curriculum" in result
            assert len(result["curriculum"]) > 0
            assert "messages" in result
    
    def test_curriculum_fallback_on_parse_error(self, empty_state):
        """Curriculum agent should create fallback on JSON parse error."""
        from agents import curriculum_agent
        
        empty_state["topic"] = "Python"
        empty_state["duration_days"] = 2
        
        with patch("agents.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(content="invalid json")
            mock_get_llm.return_value = mock_llm
            
            result = curriculum_agent(empty_state)
            
            assert "curriculum" in result
            assert len(result["curriculum"]) == 2  # Fallback creates 2 days


class TestConfirmAgent:
    """Tests for the confirm curriculum agent."""
    
    def test_confirm_positive_response(self, state_with_curriculum):
        """Confirm agent should accept 'yes'."""
        from agents import confirm_curriculum_agent
        
        state_with_curriculum["messages"] = [HumanMessage(content="yes")]
        
        result = confirm_curriculum_agent(state_with_curriculum)
        
        assert result["curriculum_confirmed"] == True
        assert result["current_day"] == 1
    
    def test_confirm_negative_response(self, state_with_curriculum):
        """Confirm agent should reject 'no'."""
        from agents import confirm_curriculum_agent
        
        state_with_curriculum["messages"] = [HumanMessage(content="no")]
        
        result = confirm_curriculum_agent(state_with_curriculum)
        
        assert result["curriculum_confirmed"] == False


class TestTodoAgent:
    """Tests for the todo agent."""
    
    def test_todo_with_no_curriculum(self, empty_state):
        """Todo agent should handle missing curriculum."""
        from agents import todo_agent
        
        result = todo_agent(empty_state)
        
        assert "messages" in result
        assert len(result.get("todos", [])) == 0
    
    def test_todo_generates_tasks(self, state_with_curriculum):
        """Todo agent should generate tasks for current day."""
        from agents import todo_agent
        
        with patch("agents.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(
                content="□ Task 1 (15 min)\n□ Task 2 (20 min)"
            )
            mock_get_llm.return_value = mock_llm
            
            result = todo_agent(state_with_curriculum)
            
            assert "todos" in result
            assert len(result["todos"]) > 0


class TestProgressAgent:
    """Tests for the progress agent."""
    
    def test_progress_with_no_curriculum(self, empty_state):
        """Progress agent should handle missing curriculum."""
        from agents import progress_agent
        
        result = progress_agent(empty_state)
        
        assert "messages" in result
    
    def test_progress_calculates_correctly(self, state_with_curriculum):
        """Progress agent should calculate progress correctly."""
        from agents import progress_agent
        
        state_with_curriculum["completed_days"] = [1]
        
        result = progress_agent(state_with_curriculum)
        
        assert "messages" in result
        content = result["messages"][0].content
        assert "50%" in content or "1/2" in content


class TestQuizGrader:
    """Tests for the quiz grader agent."""
    
    def test_grader_with_no_quiz(self, empty_state):
        """Grader should handle missing quiz."""
        from agents import quiz_grader_agent
        
        result = quiz_grader_agent(empty_state)
        
        assert "messages" in result
    
    def test_grader_scores_correctly(self, state_with_quiz):
        """Grader should score answers correctly."""
        from agents import quiz_grader_agent
        
        state_with_quiz["messages"] = [HumanMessage(content="b, b")]
        
        result = quiz_grader_agent(state_with_quiz)
        
        assert result["quiz_score"] == 100  # Both answers are 'b'
        assert result["quizzes_taken"] == 1


class TestCompleteDayAgent:
    """Tests for the complete day agent."""
    
    def test_complete_advances_day(self, state_with_curriculum):
        """Complete agent should advance to next day."""
        from agents import complete_day_agent
        
        result = complete_day_agent(state_with_curriculum)
        
        assert result["current_day"] == 2
        assert 1 in result["completed_days"]
    
    def test_complete_final_day(self, state_with_curriculum):
        """Complete agent should handle course completion."""
        from agents import complete_day_agent
        
        state_with_curriculum["current_day"] = 2
        state_with_curriculum["completed_days"] = [1]
        
        result = complete_day_agent(state_with_curriculum)
        
        assert 2 in result["completed_days"]
        assert "CONGRATULATIONS" in result["messages"][0].content
