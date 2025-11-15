"""
Test suite for configuration file functionality.
"""

import sys
import os
import tempfile
import yaml

# Add src to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config_file import ConfigManager


def test_config_manager_default():
    """Test ConfigManager with default configuration."""
    print("Testing ConfigManager with default configuration...")
    
    # Create a ConfigManager instance without a config file
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "nonexistent_config.yaml")
        config_manager = ConfigManager(config_path)
        
        # Verify default values are used
        assert config_manager.get_max_query_length() == 500
        assert config_manager.get_max_queries_per_session() == 100
        assert "show" in config_manager.get_allowed_commands()
        assert "reload" in config_manager.get_blocked_keywords()
        assert config_manager.is_file_logging_enabled() is True
        assert config_manager.get_connection_timeout() == 30
        assert config_manager.get_default_model() == "llama-3.3-70b-versatile"
        
        print("✓ Default configuration test passed")


def test_config_manager_from_file():
    """Test ConfigManager with configuration from file."""
    print("Testing ConfigManager with configuration from file...")
    
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
        
        # Create ConfigManager with the custom config file
        config_manager = ConfigManager(config_path)
        
        # Verify custom values are loaded
        assert config_manager.get_max_query_length() == 1000
        assert config_manager.get_max_queries_per_session() == 50
        assert "test" in config_manager.get_allowed_commands()
        assert "custom" in config_manager.get_allowed_commands()
        assert "dangerous" in config_manager.get_blocked_keywords()
        assert "forbidden" in config_manager.get_blocked_keywords()
        assert config_manager.is_console_logging_enabled() is True
        assert config_manager.get_connection_timeout() == 60
        assert config_manager.get_default_model() == "custom-model"
        assert config_manager.get_temperature() == 0.5
        assert config_manager.is_verbose_mode() is True
        assert config_manager.get_max_commands_per_minute() == 15
        
        print("✓ Configuration from file test passed")


def test_config_manager_validation():
    """Test ConfigManager configuration validation."""
    print("Testing ConfigManager configuration validation...")
    
    # Create a config with invalid values
    invalid_config = {
        "security": {
            "max_query_length": -100,  # Invalid: negative
            "max_queries_per_session": "not_a_number",  # Invalid: not a number
            "allowed_commands": "not_a_list",  # Invalid: not a list
            "blocked_keywords": None  # Invalid: None
        },
        "logging": {
            "enable_console": "not_a_bool",  # Invalid: not a boolean
            "log_level": "INVALID_LEVEL"  # Invalid: not in valid levels
        },
        "connection": {
            "max_reconnect_attempts": -5,  # Invalid: negative
            "connection_timeout": 0  # Invalid: zero or negative
        }
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "invalid_config.yaml")
        
        # Write the invalid config to file
        with open(config_path, 'w') as f:
            yaml.dump(invalid_config, f)
        
        # Create ConfigManager with the invalid config file
        config_manager = ConfigManager(config_path)
        
        # Validation should fix invalid values to defaults
        assert config_manager.get_max_query_length() > 0  # Should be positive
        assert config_manager.get_max_queries_per_session() > 0  # Should be positive
        assert isinstance(config_manager.get_allowed_commands(), list)  # Should be list
        assert isinstance(config_manager.get_blocked_keywords(), list)  # Should be list
        assert isinstance(config_manager.is_console_logging_enabled(), bool)  # Should be bool
        
        print("✓ Configuration validation test passed")


def test_config_manager_reload():
    """Test ConfigManager configuration reloading."""
    print("Testing ConfigManager configuration reloading...")
    
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
        
        # Create ConfigManager
        config_manager = ConfigManager(config_path)
        
        # Verify initial values
        assert config_manager.get_max_query_length() == 500
        
        # Update the file with new config
        with open(config_path, 'w') as f:
            yaml.dump(updated_config, f)
        
        # Reload the config
        config_manager.reload_config()
        
        # Verify updated values
        assert config_manager.get_max_query_length() == 1000
        assert config_manager.get_max_queries_per_session() == 200
        
        print("✓ Configuration reload test passed")


def test_config_manager_update():
    """Test ConfigManager configuration updating."""
    print("Testing ConfigManager configuration updating...")
    
    # Create a ConfigManager with default config
    config_manager = ConfigManager()
    
    # Update with new values
    new_config = {
        "security": {
            "max_query_length": 2000
        },
        "agent": {
            "default_model": "updated-model"
        }
    }
    
    config_manager.update_config(new_config)
    
    # Verify updated values
    assert config_manager.get_max_query_length() == 2000
    assert config_manager.get_default_model() == "updated-model"
    
    # Verify other values remain unchanged
    assert config_manager.get_connection_timeout() == 30  # Default value
    
    print("✓ Configuration update test passed")


def run_all_tests():
    """Run all configuration tests."""
    print("Running Configuration Test Suite...\n")
    
    test_config_manager_default()
    test_config_manager_from_file()
    test_config_manager_validation()
    test_config_manager_reload()
    test_config_manager_update()
    
    print("\n🎉 All Configuration Tests Passed!")
    print("✅ Default configuration handling")
    print("✅ File-based configuration loading")
    print("✅ Configuration validation")
    print("✅ Configuration reloading")
    print("✅ Configuration updating")


if __name__ == "__main__":
    run_all_tests()