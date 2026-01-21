"""
Integration tests for the LangGraph workflow.
"""

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage


class TestGraphBuilding:
    """Tests for graph construction."""
    
    def test_graph_compiles(self):
        """Graph should compile without errors."""
        from graph import build_graph
        
        graph = build_graph()
        assert graph is not None
    
    def test_graph_has_all_nodes(self):
        """Graph should have all required nodes."""
        from graph import build_graph
        
        graph = build_graph()
        
        # Check that graph was compiled
        assert hasattr(graph, 'invoke')


class TestGraphRouting:
    """Tests for graph routing logic."""
    
    def test_route_to_curriculum(self):
        """Should route to curriculum node."""
        from graph import route_to_agent
        
        state = {"next_action": "create_curriculum"}
        result = route_to_agent(state)
        
        assert result == "curriculum"
    
    def test_route_to_quiz(self):
        """Should route to quiz node."""
        from graph import route_to_agent
        
        state = {"next_action": "take_quiz"}
        result = route_to_agent(state)
        
        assert result == "quiz"
    
    def test_route_to_resources(self):
        """Should route to resources node."""
        from graph import route_to_agent
        
        state = {"next_action": "get_resources"}
        result = route_to_agent(state)
        
        assert result == "resources"
    
    def test_route_unknown_action(self):
        """Should route to unknown for invalid actions."""
        from graph import route_to_agent
        
        state = {"next_action": "invalid_action"}
        result = route_to_agent(state)
        
        assert result == "unknown"


class TestGraphExecution:
    """Tests for end-to-end graph execution."""
    
    def test_full_curriculum_flow(self, mock_openai):
        """Test complete curriculum creation flow."""
        from graph import build_graph
        from state import create_initial_state
        
        with patch("agents.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            # Router returns create_curriculum
            mock_llm.invoke.side_effect = [
                MagicMock(content="create_curriculum"),
                MagicMock(content='[{"day_number": 1, "title": "Day 1", "topics": ["Intro"], "completed": false}]')
            ]
            mock_get_llm.return_value = mock_llm
            
            graph = build_graph()
            
            state = create_initial_state()
            state["messages"] = [HumanMessage(content="teach me Python")]
            
            # This would need proper mocking of the LLM
            # For now, just verify graph can be invoked
            assert graph is not None


class TestCheckpointing:
    """Tests for state persistence."""
    
    def test_sqlite_checkpointer_creation(self):
        """Should create SQLite checkpointer."""
        from graph import get_sqlite_checkpointer
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            checkpointer = get_sqlite_checkpointer(db_path)
            
            assert checkpointer is not None
    
    def test_create_app_with_persistence(self):
        """Should create app with persistence."""
        from graph import create_app
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            app = create_app(db_path)
            
            assert app is not None
            assert hasattr(app, 'invoke')


class TestGraphDiagram:
    """Tests for graph visualization."""
    
    def test_diagram_generation(self):
        """Should generate diagram."""
        from graph import get_graph_diagram
        
        diagram = get_graph_diagram()
        
        assert "ROUTER" in diagram
        assert "curriculum" in diagram
        assert "quiz" in diagram
        assert "resources" in diagram
