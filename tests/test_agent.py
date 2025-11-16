"""Tests for the Agent class."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.agent import Agent, AgentState
from src.network_device import DeviceConnection
from src.audit import AuditLogger
from src.security import CommandSecurityPolicy
from src.exceptions import CommandBlockedError


class TestAgent(unittest.TestCase):
    """Test cases for the Agent class."""

    def setUp(self):
        """Set up the test case."""
        self.mock_device = Mock(spec=DeviceConnection)
        self.mock_audit_logger = Mock(spec=AuditLogger)
        self.mock_security_policy = Mock(spec=CommandSecurityPolicy)

        # Patch the CommandSecurityPolicy to return our mock
        with patch('src.agent.CommandSecurityPolicy', return_value=self.mock_security_policy):
            self.agent = Agent(
                groq_api_key='test_key',
                device=self.mock_device,
                model_name='test-model',
                audit_logger=self.mock_audit_logger
            )

    @patch('src.agent.ChatGroq')
    @patch('src.agent.CommandSecurityPolicy')
    def test_agent_initialization(self, mock_security_policy_class, mock_chat_groq):
        """Test agent initialization."""
        mock_llm = Mock()
        mock_chat_groq.return_value = mock_llm
        mock_security_policy = Mock(spec=CommandSecurityPolicy)
        mock_security_policy_class.return_value = mock_security_policy

        agent = Agent(
            groq_api_key='test_key',
            device=self.mock_device,
            model_name='test-model',
            audit_logger=self.mock_audit_logger
        )

        self.assertEqual(agent.model_name, 'test-model')
        self.assertEqual(agent.groq_api_key, 'test_key')
        self.assertIsNotNone(agent.data_protector)
        self.assertIsNotNone(agent.security_policy)
        mock_chat_groq.assert_called_once()

    @patch('src.agent.CommandSecurityPolicy')
    @patch('src.agent.ChatGroq')
    def test_execute_device_command_valid(self, mock_chat_groq, mock_security_policy_class):
        """Test executing a valid device command."""
        # Setup
        mock_llm = Mock()
        mock_chat_groq.return_value = mock_llm
        mock_security_policy = Mock(spec=CommandSecurityPolicy)
        mock_security_policy.validate_command.return_value = None  # Valid command doesn't raise exception
        mock_security_policy_class.return_value = mock_security_policy

        agent = Agent(
            groq_api_key='test_key',
            device=self.mock_device,
            model_name='test-model',
            audit_logger=self.mock_audit_logger
        )

        # Execute command
        self.mock_device.execute_command.return_value = "Command output"
        result = agent._execute_device_command("show version")

        # Assertions
        mock_security_policy.validate_command.assert_called_once_with("show version")
        self.mock_device.execute_command.assert_called_once_with("show version")
        self.mock_audit_logger.log_command_executed.assert_called_once_with(
            "show version", success=True, output_length=len("Command output")
        )
        self.assertEqual(result, "Command output")

    @patch('src.agent.CommandSecurityPolicy')
    @patch('src.agent.ChatGroq')
    def test_execute_device_command_blocked(self, mock_chat_groq, mock_security_policy_class):
        """Test executing a blocked device command."""
        # Setup
        mock_llm = Mock()
        mock_chat_groq.return_value = mock_llm
        mock_security_policy = Mock(spec=CommandSecurityPolicy)
        mock_security_policy.validate_command.side_effect = CommandBlockedError("reload", "Blocked keyword 'reload'")
        mock_security_policy_class.return_value = mock_security_policy

        agent = Agent(
            groq_api_key='test_key',
            device=self.mock_device,
            model_name='test-model',
            audit_logger=self.mock_audit_logger
        )

        # Execute command
        result = agent._execute_device_command("reload")

        # Assertions
        mock_security_policy.validate_command.assert_called_once_with("reload")
        self.mock_device.execute_command.assert_not_called()
        self.mock_audit_logger.log_command_blocked.assert_called_once_with(
            "reload", "Blocked keyword 'reload'"
        )
        self.assertEqual(result, "⚠ BLOCKED: Blocked keyword 'reload'")

    @patch('src.agent.CommandSecurityPolicy')
    @patch('src.agent.ChatGroq')
    def test_execute_device_command_connection_error(self, mock_chat_groq, mock_security_policy_class):
        """Test executing a command when connection fails."""
        # Setup
        mock_llm = Mock()
        mock_chat_groq.return_value = mock_llm
        mock_security_policy = Mock(spec=CommandSecurityPolicy)
        mock_security_policy.validate_command.return_value = None  # Valid command doesn't raise exception
        mock_security_policy_class.return_value = mock_security_policy

        agent = Agent(
            groq_api_key='test_key',
            device=self.mock_device,
            model_name='test-model',
            audit_logger=self.mock_audit_logger
        )

        # Setup connection error
        self.mock_device.execute_command.side_effect = ConnectionError("Connection failed")

        # Execute command
        result = agent._execute_device_command("show version")

        # Assertions
        mock_security_policy.validate_command.assert_called_once_with("show version")
        self.mock_device.execute_command.assert_called_once_with("show version")
        self.mock_audit_logger.log_command_executed.assert_called_once_with(
            "show version", success=False, error="Connection failed"
        )
        self.assertIn("Connection Error", result)

    @patch('src.agent.CommandSecurityPolicy')
    @patch('src.agent.ChatGroq')
    def test_execute_device_command_general_error(self, mock_chat_groq, mock_security_policy_class):
        """Test executing a command when a general error occurs."""
        # Setup
        mock_llm = Mock()
        mock_chat_groq.return_value = mock_llm
        mock_security_policy = Mock(spec=CommandSecurityPolicy)
        mock_security_policy.validate_command.return_value = None  # Valid command doesn't raise exception
        mock_security_policy_class.return_value = mock_security_policy

        agent = Agent(
            groq_api_key='test_key',
            device=self.mock_device,
            model_name='test-model',
            audit_logger=self.mock_audit_logger
        )

        # Setup general error
        self.mock_device.execute_command.side_effect = Exception("General error")

        # Execute command
        result = agent._execute_device_command("show version")

        # Assertions
        mock_security_policy.validate_command.assert_called_once_with("show version")
        self.mock_device.execute_command.assert_called_once_with("show version")
        self.mock_audit_logger.log_command_executed.assert_called_once_with(
            "show version", success=False, error="General error"
        )
        self.assertIn("Error:", result)

    def test_agent_state_typed_dict(self):
        """Test AgentState TypedDict structure."""
        state = AgentState(messages=[])
        self.assertEqual(state['messages'], [])


if __name__ == "__main__":
    unittest.main()