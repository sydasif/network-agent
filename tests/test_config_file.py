"""
Test suite for application configuration functionality.
"""

import sys
import os
import tempfile
import yaml

# Add src to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import Config


def test_config_default():
    """Test Config with default configuration."""
    print("Testing Config with default configuration...")

    # Create a Config instance without a config file
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "nonexistent_config.yaml")
        config = Config(config_path)

        # Verify default values are used
        assert config.app.security.max_query_length == 500
        assert config.app.security.max_queries_per_session == 100
        assert "show" in config.app.security.allowed_commands
        assert "reload" in config.app.security.blocked_keywords
        assert config.app.logging.enable_file is True
        assert config.app.connection.connection_timeout == 30
        assert config.app.agent.default_model == "llama-3.3-70b-versatile"

        print("✓ Default configuration test passed")


def test_config_from_file():
    """Test Config with configuration from file."""
    print("Testing Config with configuration from file...")

    # Create a temporary config file with custom values
    custom_config = {
        "security": {
            "max_query_length": 1000,
            "max_queries_per_session": 50,
            "allowed_commands": ["test", "custom"],
            "blocked_keywords": ["dangerous", "forbidden"]
        },
        "logging": {
            "enable_console": True,
            "enable_file": False,
            "enable_json": False,
            "log_level": "DEBUG"
        },
        "connection": {
            "max_reconnect_attempts": 5,
            "connection_timeout": 60,
            "read_timeout": 120,
            "command_timeout": 90
        },
        "agent": {
            "default_model": "custom-model",
            "temperature": 0.5,
            "platform_type": "Custom Platform",
            "verbose_mode": True,
            "api_timeout": 120
        },
        "limits": {
            "max_commands_per_minute": 15,
            "max_session_duration_minutes": 60
        }
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "custom_config.yaml")

        # Write the custom config to file
        with open(config_path, 'w') as f:
            yaml.dump(custom_config, f)

        # Create Config with the custom config file
        config = Config(config_path)

        # Verify custom values are loaded
        assert config.app.security.max_query_length == 1000
        assert config.app.security.max_queries_per_session == 50
        assert "test" in config.app.security.allowed_commands
        assert "custom" in config.app.security.allowed_commands
        assert "dangerous" in config.app.security.blocked_keywords
        assert "forbidden" in config.app.security.blocked_keywords
        assert config.app.logging.enable_console is True
        assert config.app.connection.connection_timeout == 60
        assert config.app.agent.default_model == "custom-model"
        assert config.app.agent.temperature == 0.5
        assert config.app.agent.verbose_mode is True
        assert config.app.limits.max_commands_per_minute == 15

        print("✓ Configuration from file test passed")


def test_config_reload():
    """Test Config configuration reloading."""
    print("Testing Config configuration reloading...")

    # Create initial config
    initial_config = {
        "security": {
            "max_query_length": 500,
            "max_queries_per_session": 100
        }
    }

    # Create updated config
    updated_config = {
        "security": {
            "max_query_length": 1000,
            "max_queries_per_session": 200
        }
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "reload_config.yaml")

        # Write initial config
        with open(config_path, 'w') as f:
            yaml.dump(initial_config, f)

        # Create Config
        config = Config(config_path)

        # Verify initial values
        assert config.app.security.max_query_length == 500

        # Update the file with new config
        with open(config_path, 'w') as f:
            yaml.dump(updated_config, f)

        # Reload the config
        config.reload()

        # Verify updated values
        assert config.app.security.max_query_length == 1000
        assert config.app.security.max_queries_per_session == 200

        print("✓ Configuration reload test passed")


def run_all_tests():
    """Run all configuration tests."""
    print("Running Application Configuration Test Suite...\n")

    test_config_default()
    test_config_from_file()
    test_config_reload()

    print("\n🎉 All Configuration Tests Passed!")
    print("✅ Default configuration handling")
    print("✅ File-based configuration loading")
    print("✅ Configuration reloading")


if __name__ == "__main__":
    run_all_tests()