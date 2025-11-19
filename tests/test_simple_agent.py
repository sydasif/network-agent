"""Tests for the simplified network agent components."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agents.simple_agent import SimpleNetworkAgent, NetworkCommand
from src.core.network_manager import NetworkManager


class TestSimpleNetworkAgent:
    """Test suite for SimpleNetworkAgent class."""

    def test_initialization(self):
        """Test SimpleNetworkAgent initialization."""
        api_key = "test_api_key"

        with patch("src.agents.simple_agent.ChatGroq") as mock_chat_groq:
            mock_llm = Mock()
            mock_chat_groq.return_value = mock_llm
            mock_llm.with_structured_output = Mock(return_value=Mock())
            
            agent = SimpleNetworkAgent(api_key=api_key)

            # Verify that ChatGroq was called with the correct parameters
            mock_chat_groq.assert_called_once()
            call_args = mock_chat_groq.call_args
            assert call_args[1]["groq_api_key"] == api_key
            assert call_args[1]["model_name"] == "llama3-70b-4096"

    def test_process_request(self):
        """Test process_request method."""
        api_key = "test_api_key"

        with patch("src.agents.simple_agent.ChatGroq"):
            # Mock the NetworkManager to avoid actual Nornir initialization
            with patch("src.agents.simple_agent.NetworkManager") as mock_network_mgr_class:
                # Create a mock network manager instance
                mock_network_instance = Mock()
                mock_network_instance.get_device_names.return_value = ["R1", "S1"]
                mock_network_instance.execute_command.return_value = "Mock command output"

                mock_network_mgr_class.return_value = mock_network_instance

                agent = SimpleNetworkAgent(api_key=api_key)

                # Mock the extractor to return a known result
                with patch.object(agent, 'extractor') as mock_extractor:
                    mock_extractor.invoke.return_value = NetworkCommand(
                        device_name="R1",
                        command="show version"
                    )

                    result = agent.process_request("show version on R1")

                    # Verify the result
                    assert result["device_name"] == "R1"
                    assert result["command"] == "show version"
                    assert result["output"] == "Mock command output"

                    # Verify the extractor and network manager were called correctly
                    mock_extractor.invoke.assert_called_once()
                    mock_network_instance.execute_command.assert_called_once_with("R1", "show version")

    def test_close_sessions(self):
        """Test close_sessions method."""
        api_key = "test_api_key"

        with patch("src.agents.simple_agent.ChatGroq"):
            # Mock the NetworkManager to avoid actual Nornir initialization
            with patch("src.agents.simple_agent.NetworkManager") as mock_network_mgr_class:
                mock_network_instance = Mock()
                mock_network_mgr_class.return_value = mock_network_instance

                agent = SimpleNetworkAgent(api_key=api_key)

                agent.close_sessions()

                # Verify that close_all_sessions was called on the network manager
                mock_network_instance.close_all_sessions.assert_called_once()


class TestNetworkManager:
    """Test suite for NetworkManager class."""

    def test_initialization(self):
        """Test NetworkManager initialization."""
        with patch("src.core.network_manager.InitNornir") as mock_init_nornir:
            mock_nornir = Mock()
            mock_init_nornir.return_value = mock_nornir
            mock_nornir.inventory = Mock()
            mock_nornir.inventory.hosts = {"R1": Mock(), "S1": Mock()}

            manager = NetworkManager(config_file="test_config.yaml")

            # Verify Nornir was initialized with the correct config
            mock_init_nornir.assert_called_once_with(config_file="test_config.yaml")

    def test_get_device_names(self):
        """Test get_device_names method."""
        with patch("src.core.network_manager.InitNornir") as mock_init_nornir:
            mock_nornir = Mock()
            mock_init_nornir.return_value = mock_nornir
            mock_nornir.inventory = Mock()
            mock_nornir.inventory.hosts = {"R1": Mock(), "S1": Mock(), "S2": Mock()}

            manager = NetworkManager()
            device_names = manager.get_device_names()

            assert device_names == ["R1", "S1", "S2"]

    def test_execute_command(self):
        """Test execute_command method."""
        with patch("src.core.network_manager.InitNornir") as mock_init_nornir:
            mock_nornir = Mock()
            mock_filtered_nornir = Mock()

            # Mock the filter method to return the filtered nornir
            mock_nornir.filter.return_value = mock_filtered_nornir

            # Mock the inventory hosts to return proper data for len()
            mock_filtered_inventory = Mock()
            mock_filtered_inventory.hosts = {"R1": Mock()}  # This makes len() work
            mock_filtered_nornir.inventory = mock_filtered_inventory

            # Mock the run method to return results
            mock_result = Mock()
            mock_result.__getitem__ = Mock()
            mock_result.__getitem__.return_value.failed = False
            mock_result.__getitem__.return_value.result = "Command output"
            mock_filtered_nornir.run.return_value = mock_result

            mock_init_nornir.return_value = mock_nornir
            mock_nornir.inventory = Mock()
            mock_nornir.inventory.hosts = {"R1": Mock()}

            manager = NetworkManager()
            output = manager.execute_command("R1", "show version")

            assert output == "Command output"
            mock_nornir.filter.assert_called_once_with(name="R1")
            mock_filtered_nornir.run.assert_called_once()

    def test_execute_command_device_not_found(self):
        """Test execute_command raises exception when device not found."""
        with patch("src.core.network_manager.InitNornir") as mock_init_nornir:
            mock_nornir = Mock()
            
            # Mock the filter method to return no hosts
            mock_filtered_nornir = Mock()
            mock_filtered_nornir.inventory = Mock()
            mock_filtered_nornir.inventory.hosts = {}  # Empty hosts
            mock_nornir.filter.return_value = mock_filtered_nornir
            
            mock_init_nornir.return_value = mock_nornir
            mock_nornir.inventory = Mock()
            mock_nornir.inventory.hosts = {}  # No hosts in inventory

            manager = NetworkManager()
            
            with pytest.raises(ValueError, match="Device 'R1' not found in inventory."):
                manager.execute_command("R1", "show version")

    def test_execute_command_on_multiple_devices(self):
        """Test execute_command_on_multiple_devices method."""
        with patch("src.core.network_manager.InitNornir") as mock_init_nornir:
            mock_nornir = Mock()
            mock_filtered_nornir = Mock()

            # Mock the filter method to return the filtered nornir
            mock_nornir.filter.return_value = mock_filtered_nornir

            # Mock the inventory hosts to return proper data for len()
            mock_filtered_inventory = Mock()
            mock_filtered_inventory.hosts = {"R1": Mock(), "S1": Mock(), "S2": Mock()}
            mock_filtered_nornir.inventory = mock_filtered_inventory

            # Mock the run method to return results for multiple devices
            mock_result = Mock()

            # Create a side_effect function for __getitem__
            def getitem_side_effect(key):
                item_result = Mock()
                if key == "R1":
                    item_result.failed = False
                    item_result.result = "R1 output"
                elif key == "S1":
                    item_result.failed = False
                    item_result.result = "S1 output"
                elif key == "S2":
                    item_result.failed = True
                    item_result.result = "Error occurred"
                else:
                    # For devices not in results
                    item_result.failed = True
                    item_result.result = "Device not found in results"
                return item_result

            # Set up the side effect for getitem
            mock_result.__getitem__ = Mock(side_effect=getitem_side_effect)

            mock_filtered_nornir.run.return_value = mock_result

            mock_init_nornir.return_value = mock_nornir
            mock_nornir.inventory = Mock()
            mock_nornir.inventory.hosts = {"R1": Mock(), "S1": Mock(), "S2": Mock()}

            manager = NetworkManager()
            outputs = manager.execute_command_on_multiple_devices(
                ["R1", "S1", "S2"], "show version"
            )

            expected_outputs = {
                "R1": "R1 output",
                "S1": "S1 output",
                "S2": "Error: Error occurred"
            }
            assert outputs == expected_outputs