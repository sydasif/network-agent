"""Tests for the NetworkWorkflow class."""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage
from src.graph.workflow import NetworkWorkflow


class TestNetworkWorkflow:
    """Test suite for NetworkWorkflow class."""

    def test_initialization(self):
        """Test NetworkWorkflow initialization."""
        api_key = "test_api_key"
        with patch("src.graph.workflow.ChatGroq") as mock_chat_groq:
            mock_llm = Mock()
            mock_chat_groq.return_value = mock_llm
            mock_llm.with_structured_output = Mock()

            workflow = NetworkWorkflow(api_key=api_key)

            # Verify that ChatGroq was called with the correct parameters
            mock_chat_groq.assert_called_once()
            call_args = mock_chat_groq.call_args
            assert call_args[1]["groq_api_key"] == api_key

    def test_run_method_calls_graph_invoke(self):
        """Test that run method calls the graph with correct inputs."""
        api_key = "test_api_key"
        query = "show interfaces"
        chat_history = [HumanMessage(content="Hello"), AIMessage(content="Hi")]

        with patch("src.graph.workflow.ChatGroq") as mock_chat_groq:
            mock_llm = Mock()
            mock_chat_groq.return_value = mock_llm
            mock_llm.with_structured_output = Mock()

            workflow = NetworkWorkflow(api_key=api_key)

            # Mock the graph and its invoke method
            mock_graph = Mock()
            mock_graph.invoke = Mock(return_value={"response": "test response"})
            workflow.graph = mock_graph

            result = workflow.run(query, chat_history)

            # Verify that graph.invoke was called with the correct inputs
            mock_graph.invoke.assert_called_once()
            call_args = mock_graph.invoke.call_args[0][0]
            assert call_args["input"] == query
            assert call_args["chat_history"] == chat_history
            assert result == "test response"

    def test_preprocessor_node_greeting_intent(self):
        """Test preprocessor node handling greeting intents."""
        api_key = "test_api_key"

        with patch("src.graph.workflow.ChatGroq") as mock_chat_groq:
            mock_llm = Mock()
            mock_chat_groq.return_value = mock_llm
            mock_llm.with_structured_output = Mock()

            workflow = NetworkWorkflow(api_key=api_key)

            state = {"input": "hello", "chat_history": []}

            # Test the preprocessor_node directly
            result = workflow.preprocessor_node(state)

            # Should return a greeting response
            assert "structured_intent" in result
            assert "response" in result
            assert (
                result["response"]
                == "Hello! I'm your network assistant. How can I help?"
            )

    def test_preprocessor_node_with_exception_handling(self):
        """Test preprocessor node handling exceptions gracefully."""
        api_key = "test_api_key"

        with patch("src.graph.workflow.ChatGroq") as mock_chat_groq:
            mock_llm = Mock()
            mock_chat_groq.return_value = mock_llm
            mock_llm.with_structured_output = Mock()

            # Configure the mock to raise an exception when invoked
            mock_llm.with_structured_output.return_value.invoke.side_effect = Exception(
                "Test error"
            )

            workflow = NetworkWorkflow(api_key=api_key)

            state = {"input": "some query that causes error", "chat_history": []}

            # Test that it doesn't crash but returns appropriate fallback
            result = workflow.preprocessor_node(state)

            # Should handle the exception and return appropriate response
            assert "structured_intent" in result
