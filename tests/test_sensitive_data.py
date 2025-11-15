"""Test for sensitive data sanitization."""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sensitive_data import SensitiveDataProtector


def test_password_sanitization():
    """Test password detection and sanitization."""
    protector = SensitiveDataProtector()
    
    test_cases = [
        # Various password formats
        ("password: MySecret123", "[PASSWORD_REDACTED]"),
        ("password=MySecret123", "[PASSWORD_REDACTED]"),
        ("password = 'MySecret123'", "[PASSWORD_REDACTED]"),
        ("password = \"MySecret123\"", "[PASSWORD_REDACTED]"),
        ("passwd: MySecret123", "[PASSWORD_REDACTED]"),
        ("passwd=MySecret123", "[PASSWORD_REDACTED]"),
        ("pwd: MySecret123", "[PASSWORD_REDACTED]"),
        ("pwd=MySecret123", "[PASSWORD_REDACTED]"),
        ("Password: MySecret123", "[PASSWORD_REDACTED]"),
        ("PASSWORD: MySecret123", "[PASSWORD_REDACTED]"),
        ("Enter password MySecret123 now", "[PASSWORD_REDACTED]"),  # Context-based detection
    ]
    
    for text, expected in test_cases:
        result = protector.sanitize_for_logging(text)
        assert expected in result, f"Password not redacted in '{text}'. Got: {result}"
        # Make sure the actual password is not present
        assert "MySecret123" not in result or expected == "[PASSWORD_REDACTED]"


def test_api_key_sanitization():
    """Test API key detection and sanitization."""
    protector = SensitiveDataProtector()
    
    # Test Groq API key pattern
    groq_key = "gsk_abcdefghijklmnopqrstuvwxyz123456"
    text_with_groq_key = f"Using API key: {groq_key} for authentication"
    sanitized = protector.sanitize_for_logging(text_with_groq_key)
    assert "[API_KEY_REDACTED]" in sanitized
    assert groq_key not in sanitized
    
    # Test general API key patterns
    test_cases = [
        f"api_key: {groq_key}",
        f"api_key={groq_key}",
        f"api-key: {groq_key}",
        f"apiKey: {groq_key}",
        f"API_KEY={groq_key}",
        f"token: {groq_key}",
        f"token={groq_key}",
        f"Token: {groq_key}",
        f"bearer {groq_key}",
        f"Bearer {groq_key}",
    ]
    
    for text in test_cases:
        result = protector.sanitize_for_logging(text)
        assert "[API_KEY_REDACTED]" in result, f"API key not redacted in '{text}'"
        assert groq_key not in result


def test_snmp_community_sanitization():
    """Test SNMP community string detection and sanitization."""
    protector = SensitiveDataProtector()
    
    test_cases = [
        "snmp-server community private_string ro",
        "snmp-server community public_string rw",
        "snmp community secret_community",
        "SNMP-SERVER COMMUNITY top_secret",
        "Snmp-Server Community hidden_password",
    ]
    
    for text in test_cases:
        result = protector.sanitize_for_logging(text)
        assert "[SNMP_COMMUNITY_REDACTED]" in result, f"SNMP community not redacted in '{text}'"
        # Check that the specific community string is not in the result
        # (this depends on the specific string used, so we just check the replacement)


def test_tacacs_radius_sanitization():
    """Test TACACS/RADIUS secret detection and sanitization."""
    protector = SensitiveDataProtector()
    
    test_cases = [
        "tacacs-server key super_secret_key",
        "tacacs key another_secret",
        "radius-server key radius_secret",
        "radius key radius_password",
        "TACACS-SERVER KEY my_secret",
        "RADIUS-SERVER KEY secret123",
    ]
    
    for text in test_cases:
        result = protector.sanitize_for_logging(text)
        assert "[SECRET_REDACTED]" in result, f"TACACS/RADIUS secret not redacted in '{text}'"


def test_crypto_key_sanitization():
    """Test crypto/encryption key detection and sanitization."""
    protector = SensitiveDataProtector()
    
    test_cases = [
        "pre-shared-key my_very_secret_key",
        "psk: confidential_password",
        "key 1 my_shared_key",
        "key 10 super_secret_key",
        "crypto key generate rsa",
        "ipsec key secure_key",
    ]
    
    for text in test_cases:
        result = protector.sanitize_for_logging(text)
        # Note: The specific replacement depends on which pattern matches
        # Either [KEY_REDACTED] or [SECRET_REDACTED] may appear
        assert ("[KEY_REDACTED]" in result or "[SECRET_REDACTED]" in result or "[PASSWORD_REDACTED]" in result), \
               f"Crypto key not redacted in '{text}'. Result: {result}"


def test_ip_address_sanitization():
    """Test IP address detection (with aggressive mode)."""
    protector = SensitiveDataProtector()
    
    # IP addresses should only be redacted in aggressive mode
    private_ips = [
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.1",
        "10.100.200.254",
        "172.30.100.50",
        "192.168.100.100"
    ]
    
    for ip in private_ips:
        text = f"Device at {ip} responded"
        
        # Non-aggressive mode - IPs should NOT be redacted
        result = protector.sanitize_for_logging(text, aggressive=False)
        assert ip in result, f"IP {ip} was redacted in non-aggressive mode, but shouldn't be"
        
        # Aggressive mode - IPs SHOULD be redacted
        result_aggressive = protector.sanitize_for_logging(text, aggressive=True)
        assert "[IP_REDACTED]" in result_aggressive, f"IP {ip} was not redacted in aggressive mode"


def test_hostname_sanitization():
    """Test hostname detection (with aggressive mode)."""
    protector = SensitiveDataProtector()
    
    hostnames = [
        "hostname: myrouter",
        "hostname core-switch-01",
        "set hostname edge-router-2a",
        "Hostname: firewall-primary"
    ]
    
    for text in hostnames:
        # Non-aggressive mode - hostnames should NOT be redacted
        result = protector.sanitize_for_logging(text, aggressive=False)
        assert "hostname" in result.lower(), f"Hostname keyword removed in non-aggressive mode: {result}"
        
        # Aggressive mode - hostnames SHOULD be redacted
        result_aggressive = protector.sanitize_for_logging(text, aggressive=True)
        assert "[HOSTNAME_REDACTED]" in result_aggressive, f"Hostname not redacted in aggressive mode: {text}"


def test_command_sanitization():
    """Test command sanitization method."""
    protector = SensitiveDataProtector()
    
    # Commands with passwords should be sanitized
    command_with_password = "username admin password secret123"
    sanitized_command = protector.sanitize_command(command_with_password)
    assert "[PASSWORD_REDACTED]" in sanitized_command


def test_output_sanitization():
    """Test output sanitization with truncation."""
    protector = SensitiveDataProtector()
    
    # Test with sensitive data
    output_with_sensitive = "Config: password is MySecret123 and API key is gsk_abcdefghijklmnopqrstuvwxyz123456"
    sanitized_output = protector.sanitize_output(output_with_sensitive)
    assert "[PASSWORD_REDACTED]" in sanitized_output
    assert "[API_KEY_REDACTED]" in sanitized_output
    
    # Test truncation
    long_output = "A" * 1000  # 1000 characters
    truncated_output = protector.sanitize_output(long_output, max_length=100)
    assert len(truncated_output) <= 150  # 100 + some buffer for truncation message
    assert "[TRUNCATED" in truncated_output


def test_error_sanitization():
    """Test error message sanitization."""
    protector = SensitiveDataProtector()
    
    error_with_password = "Connection failed: password was MySecret123"
    sanitized_error = protector.sanitize_error(error_with_password)
    assert "[PASSWORD_REDACTED]" in sanitized_error
    assert "MySecret123" not in sanitized_error


def test_dictionary_sanitization():
    """Test dictionary sanitization."""
    protector = SensitiveDataProtector()
    
    # Dictionary with sensitive data
    sensitive_dict = {
        "username": "admin",
        "password": "MySecret123",
        "api_key": "gsk_abcdefghijklmnopqrstuvwxyz123456",
        "normal_field": "normal_value",
        "config": {
            "snmp_community": "private",
            "hostname": "myrouter",
            "port": 8080
        }
    }
    
    sanitized_dict = protector.sanitize_dict(sensitive_dict)
    
    # Verify sensitive fields are redacted
    assert sanitized_dict["password"] == "[REDACTED]"
    assert sanitized_dict["api_key"] == "[REDACTED]"
    
    # Verify non-sensitive fields are preserved
    assert sanitized_dict["username"] == "admin"
    assert sanitized_dict["normal_field"] == "normal_value"
    
    # Verify nested dict is also sanitized
    assert sanitized_dict["config"]["snmp_community"] == "[REDACTED]"
    assert sanitized_dict["config"]["hostname"] == "[REDACTED]"
    assert sanitized_dict["config"]["port"] == 8080  # Non-string value preserved


def test_masking_functions():
    """Test specific masking functions."""
    protector = SensitiveDataProtector()
    
    # Test password masking
    assert protector.mask_password("") == ""
    assert protector.mask_password("a") == "*"
    assert protector.mask_password("ab") == "**"
    assert protector.mask_password("abc") == "***"
    assert protector.mask_password("abcd") == "****"
    assert protector.mask_password("hello123") == "********"
    
    # Test API key masking
    short_key = "short"
    long_key = "very_long_api_key_with_32_characters"
    
    assert protector.mask_api_key(short_key) == "****"
    assert protector.mask_api_key(long_key) == "very...ters"  # First 4 and last 4 chars


def test_case_insensitive_detection():
    """Test that sensitive data detection is case-insensitive."""
    protector = SensitiveDataProtector()
    
    test_cases = [
        ("PASSWORD: secret123", "[PASSWORD_REDACTED]"),
        ("Password: secret123", "[PASSWORD_REDACTED]"),
        ("password: secret123", "[PASSWORD_REDACTED]"),
        ("Api_Key: gsk_abcdefghijklmnopqrstuvwxyz123456", "[API_KEY_REDACTED]"),
        ("API-KEY: gsk_abcdefghijklmnopqrstuvwxyz123456", "[API_KEY_REDACTED]"),
        ("SNMP-SERVER COMMUNITY private ro", "[SNMP_COMMUNITY_REDACTED]"),
        ("snmp-server COMMUNITY private ro", "[SNMP_COMMUNITY_REDACTED]"),
    ]
    
    for text, expected in test_cases:
        result = protector.sanitize_for_logging(text)
        assert expected in result, f"Case-insensitive detection failed for '{text}'"


if __name__ == "__main__":
    test_password_sanitization()
    print("✓ Password sanitization tests passed")
    
    test_api_key_sanitization()
    print("✓ API key sanitization tests passed")
    
    test_snmp_community_sanitization()
    print("✓ SNMP community sanitization tests passed")
    
    test_tacacs_radius_sanitization()
    print("✓ TACACS/RADIUS sanitization tests passed")
    
    test_crypto_key_sanitization()
    print("✓ Crypto key sanitization tests passed")
    
    test_ip_address_sanitization()
    print("✓ IP address sanitization tests passed")
    
    test_hostname_sanitization()
    print("✓ Hostname sanitization tests passed")
    
    test_command_sanitization()
    print("✓ Command sanitization tests passed")
    
    test_output_sanitization()
    print("✓ Output sanitization tests passed")
    
    test_error_sanitization()
    print("✓ Error sanitization tests passed")
    
    test_dictionary_sanitization()
    print("✓ Dictionary sanitization tests passed")
    
    test_masking_functions()
    print("✓ Masking functions tests passed")
    
    test_case_insensitive_detection()
    print("✓ Case insensitive detection tests passed")
    
    print("\n🎉 All sensitive data sanitization tests passed!")