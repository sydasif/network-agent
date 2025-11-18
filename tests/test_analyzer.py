"""Tests for the ProactiveAnalyzer class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agents.analyzer import ProactiveAnalyzer


class TestProactiveAnalyzer:
    """Test suite for ProactiveAnalyzer class."""

    def test_initialization(self):
        """Test ProactiveAnalyzer initialization."""
        api_key = "test_api_key"

        with patch("src.agents.analyzer.ChatGroq") as mock_chat_groq:
            mock_llm = Mock()
            mock_chat_groq.return_value = mock_llm
            mock_llm.with_structured_output = Mock()

            analyzer = ProactiveAnalyzer(api_key=api_key)

            # Verify that ChatGroq was called with the correct parameters
            mock_chat_groq.assert_called_once()
            call_args = mock_chat_groq.call_args
            assert call_args[1]["groq_api_key"] == api_key

    def test_save_snapshot_calls_state_manager(self):
        """Test that save_snapshot calls the state manager."""
        api_key = "test_api_key"

        with patch("src.agents.analyzer.ChatGroq"):
            with patch("src.agents.analyzer.StateManager") as mock_state_manager:
                mock_state_manager_instance = Mock()
                mock_state_manager.return_value = mock_state_manager_instance

                analyzer = ProactiveAnalyzer(api_key=api_key)

                device_name = "test_device"
                command = "show version"
                output = {"output": "test output"}

                analyzer.save_snapshot(device_name, command, output)

                # Verify that the state manager's save_snapshot method was called
                mock_state_manager_instance.save_snapshot.assert_called_once_with(
                    device_name, command, output
                )

    def test_load_snapshot_calls_state_manager(self):
        """Test that load_snapshot calls the state manager."""
        api_key = "test_api_key"

        with patch("src.agents.analyzer.ChatGroq"):
            with patch("src.agents.analyzer.StateManager") as mock_state_manager:
                mock_state_manager_instance = Mock()
                mock_state_manager.return_value = mock_state_manager_instance
                mock_state_manager_instance.get_latest_snapshot.return_value = {
                    "output": "test output"
                }

                analyzer = ProactiveAnalyzer(api_key=api_key)

                device_name = "test_device"
                command = "show version"

                result = analyzer.load_snapshot(device_name, command)

                # Verify that the state manager's get_latest_snapshot method was called
                mock_state_manager_instance.get_latest_snapshot.assert_called_once_with(
                    device_name, command
                )
                assert result == {"output": "test output"}

    def test_analyze_change_no_difference(self):
        """Test analyze_change with identical previous and current states."""
        api_key = "test_api_key"

        with patch("src.agents.analyzer.ChatGroq"):
            analyzer = ProactiveAnalyzer(api_key=api_key)

            device_name = "test_device"
            command = "show version"
            same_state = {"output": "same output"}

            result = analyzer.analyze_change(
                device_name, command, same_state, same_state
            )

            # Should return no change detected
            assert result["change_detected"] is False
            assert result["significance"] == "Informational"
            assert result["summary"] == "No change detected."

    def test_analyze_with_snapshot_storage_new_baseline(self):
        """Test analyze_with_snapshot_storage when no previous snapshot exists."""
        api_key = "test_api_key"

        with patch("src.agents.analyzer.ChatGroq"):
            with patch("src.agents.analyzer.StateManager") as mock_state_manager:
                mock_state_manager_instance = Mock()
                mock_state_manager.return_value = mock_state_manager_instance
                # Return None to simulate no previous snapshot
                mock_state_manager_instance.get_latest_snapshot.return_value = None

                analyzer = ProactiveAnalyzer(api_key=api_key)

                device_name = "test_device"
                command = "show version"
                new_output = {"output": "new output"}

                result = analyzer.analyze_with_snapshot_storage(
                    device_name, command, new_output
                )

                # Should return baseline stored message
                assert result["change_detected"] is False
                assert result["significance"] == "Informational"
                assert result["summary"] == "Baseline stored."

                # Verify that both save and load were called
                mock_state_manager_instance.get_latest_snapshot.assert_called_once_with(
                    device_name, command
                )
                mock_state_manager_instance.save_snapshot.assert_called_once_with(
                    device_name, command, new_output
                )

    def test_analyze_with_snapshot_storage_with_difference(self):
        """Test analyze_with_snapshot_storage when there is a difference."""
        api_key = "test_api_key"

        with patch("src.agents.analyzer.ChatGroq"):
            with patch("src.agents.analyzer.StateManager") as mock_state_manager:
                mock_state_manager_instance = Mock()
                mock_state_manager.return_value = mock_state_manager_instance
                # Return a previous state to simulate a difference
                mock_state_manager_instance.get_latest_snapshot.return_value = {
                    "output": "old output"
                }

                # Mock the LLM response for analyze_change
                with patch.object(
                    ProactiveAnalyzer, "analyze_change"
                ) as mock_analyze_change:
                    mock_analyze_change.return_value = {
                        "change_detected": True,
                        "significance": "Critical",
                        "summary": "Interface went down",
                    }

                    analyzer = ProactiveAnalyzer(api_key=api_key)

                    device_name = "test_device"
                    command = "show version"
                    new_output = {"output": "new output"}

                    result = analyzer.analyze_with_snapshot_storage(
                        device_name, command, new_output
                    )

                    # Should return the result from analyze_change
                    assert result["change_detected"] is True
                    assert result["significance"] == "Critical"
                    assert result["summary"] == "Interface went down"

                    # Verify that both save and load were called
                    mock_state_manager_instance.get_latest_snapshot.assert_called_once_with(
                        device_name, command
                    )
                    mock_state_manager_instance.save_snapshot.assert_called_once_with(
                        device_name, command, new_output
                    )
                    # Verify analyze_change was called correctly
                    mock_analyze_change.assert_called_once_with(
                        device_name, command, {"output": "old output"}, new_output
                    )
