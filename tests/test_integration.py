"""Integration tests for the network agent."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.agent import Agent
from src.network_device import DeviceConnection
from src.audit import AuditLogger
from src.security import CommandSecurityPolicy
from src.exceptions import CommandBlockedError


class TestAgentIntegration(unittest.TestCase):
    """Integration tests for the Agent class with other components."""

    def setUp(self):
        """Set up the test case."""
        self.mock_device = Mock(spec=DeviceConnection)
        self.mock_audit_logger = Mock(spec=AuditLogger)

    @patch('src.agent.CommandSecurityPolicy')
    @patch('src.agent.ChatGroq')
    def test_agent_with_valid_command(self, mock_chat_groq, mock_security_policy_class):
        """Test agent executing a valid command through full pipeline."""
        # Setup mocks
        mock_llm = Mock()
        mock_chat_groq.return_value = mock_llm
        mock_security_policy = Mock(spec=CommandSecurityPolicy)
        mock_security_policy.validate_command.return_value = None  # Valid command doesn't raise exception
        mock_security_policy_class.return_value = mock_security_policy

        # Create agent
        agent = Agent(
            groq_api_key='test_key',
            device=self.mock_device,
            model_name='test-model',
            audit_logger=self.mock_audit_logger
        )

        # Setup device response
        self.mock_device.execute_command.return_value = "Valid command output"

        # Execute command
        result = agent._execute_device_command("show version")

        # Verify all components were called correctly
        mock_security_policy.validate_command.assert_called_once_with("show version")
        self.mock_device.execute_command.assert_called_once_with("show version")
        self.mock_audit_logger.log_command_executed.assert_called_once_with(
            "show version", success=True, output_length=len("Valid command output")
        )
        self.assertEqual(result, "Valid command output")

    @patch('src.agent.CommandSecurityPolicy')
    @patch('src.agent.ChatGroq')
    def test_agent_with_blocked_command(self, mock_chat_groq, mock_security_policy_class):
        """Test agent blocking a command through security policy."""
        # Setup mocks
        mock_llm = Mock()
        mock_chat_groq.return_value = mock_llm
        mock_security_policy = Mock(spec=CommandSecurityPolicy)
        mock_security_policy.validate_command.side_effect = CommandBlockedError("reload", "Blocked keyword 'reload'")
        mock_security_policy_class.return_value = mock_security_policy

        # Create agent
        agent = Agent(
            groq_api_key='test_key',
            device=self.mock_device,
            model_name='test-model',
            audit_logger=self.mock_audit_logger
        )

        # Execute blocked command
        result = agent._execute_device_command("reload")

        # Verify command was blocked and not executed on device
        mock_security_policy.validate_command.assert_called_once_with("reload")
        self.mock_device.execute_command.assert_not_called()
        self.mock_audit_logger.log_command_blocked.assert_called_once_with(
            "reload", "Blocked keyword 'reload'"
        )
        self.assertEqual(result, "⚠ BLOCKED: Blocked keyword 'reload'")

    @patch('src.agent.CommandSecurityPolicy')
    @patch('src.agent.ChatGroq')
    def test_agent_with_connection_error(self, mock_chat_groq, mock_security_policy_class):
        """Test agent handling connection errors."""
        # Setup mocks
        mock_llm = Mock()
        mock_chat_groq.return_value = mock_llm
        mock_security_policy = Mock(spec=CommandSecurityPolicy)
        mock_security_policy.validate_command.return_value = None  # Valid command doesn't raise exception
        mock_security_policy_class.return_value = mock_security_policy

        # Create agent
        agent = Agent(
            groq_api_key='test_key',
            device=self.mock_device,
            model_name='test-model',
            audit_logger=self.mock_audit_logger
        )

        # Setup device to raise connection error
        self.mock_device.execute_command.side_effect = ConnectionError("Connection failed")

        # Execute command that will fail
        result = agent._execute_device_command("show version")

        # Verify error was handled properly
        mock_security_policy.validate_command.assert_called_once_with("show version")
        self.mock_device.execute_command.assert_called_once_with("show version")
        self.mock_audit_logger.log_command_executed.assert_called_once_with(
            "show version", success=False, error="Connection failed"
        )
        self.assertIn("Connection Error", result)


class TestSecurityIntegration(unittest.TestCase):
    """Integration tests for security components."""

    def test_command_security_policy_with_settings(self):
        """Test that security policy uses settings properly."""
        from src.security import CommandSecurityPolicy
        from src.settings import settings
        from src.exceptions import CommandBlockedError

        policy = CommandSecurityPolicy()

        # Test blocked keyword from settings
        with self.assertRaises(CommandBlockedError) as context:
            policy.validate_command("reload")
        self.assertIn("reload", str(context.exception))

        # Test allowed command from settings
        # Should not raise any exception
        try:
            policy.validate_command("show version")
            self.assertTrue(True)  # No exception raised
        except Exception:
            self.fail("validate_command raised an exception unexpectedly!")

        # Test blocked keyword that should be in settings
        with self.assertRaises(CommandBlockedError) as context:
            policy.validate_command("configure terminal")
        self.assertIn("configure", str(context.exception))


if __name__ == "__main__":
    unittest.main()