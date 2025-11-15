"""Sensitive data protection and sanitization."""

import re
from typing import Any


class SensitiveDataProtector:
    """Protect sensitive data in logs, errors, and outputs."""
    
    # Patterns for sensitive data detection
    SENSITIVE_PATTERNS = {
        # Passwords and secrets
        'password': [
            r'password\s*[:=]\s*["\']?([^"\'\s]{4,})["\']?',
            r'passwd\s*[:=]\s*["\']?([^"\'\s]{4,})["\']?',
            r'pwd\s*[:=]\s*["\']?([^"\'\s]{4,})["\']?',
            r'secret\s*["\']?([^"\'\s]{4,})["\']?',
            r'enable\s+secret\s+\d+\s+([^\s]+)',
            r'enable\s+password\s+([^\s]+)',
        ],
        # API keys and tokens
        'api_key': [
            r'api[_-]?key\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
            r'token\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
            r'bearer\s+([a-zA-Z0-9_-]{20,})',
            r'gsk_[a-zA-Z0-9]{32,}',  # Groq API key pattern
        ],
        # SNMP community strings
        'snmp': [
            r'snmp-server\s+community\s+([^\s]+)',
            r'snmp\s+community\s+([^\s]+)',
        ],
        # TACACS/RADIUS secrets
        'tacacs': [
            r'tacacs-server\s+key\s+([^\s]+)',
            r'tacacs\s+key\s+([^\s]+)',
            r'radius-server\s+key\s+([^\s]+)',
            r'radius\s+key\s+([^\s]+)',
        ],
        # Encryption keys
        'crypto': [
            r'pre-shared-key\s+([^\s]+)',
            r'psk\s+([^\s]+)',
            r'key\s+\d+\s+([^\s]+)',
        ],
        # Private IP addresses (sometimes sensitive)
        'ip': [
            r'\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            r'\b172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}\b',
            r'\b192\.168\.\d{1,3}\.\d{1,3}\b',
        ],
        # Hostnames that might reveal infrastructure
        'hostname': [
            r'hostname\s+([^\s]+)',
        ],
    }
    
    # Replacement strings
    REPLACEMENTS = {
        'password': '[PASSWORD_REDACTED]',
        'api_key': '[API_KEY_REDACTED]',
        'snmp': '[SNMP_COMMUNITY_REDACTED]',
        'tacacs': '[SECRET_REDACTED]',
        'crypto': '[KEY_REDACTED]',
        'ip': '[IP_REDACTED]',
        'hostname': '[HOSTNAME_REDACTED]',
    }
    
    @staticmethod
    def sanitize_for_logging(text: str, aggressive: bool = False) -> str:
        """Sanitize text before logging to remove sensitive data.
        
        Args:
            text: Text to sanitize
            aggressive: If True, redact more aggressively (IPs, hostnames)
            
        Returns:
            Sanitized text with sensitive data redacted
        """
        if not text:
            return text
        
        sanitized = text
        
        # Always redact passwords, keys, secrets
        critical_categories = ['password', 'api_key', 'snmp', 'tacacs', 'crypto']
        
        for category in critical_categories:
            patterns = SensitiveDataProtector.SENSITIVE_PATTERNS.get(category, [])
            replacement = SensitiveDataProtector.REPLACEMENTS.get(category, '[REDACTED]')
            
            for pattern in patterns:
                # Use re.IGNORECASE for case-insensitive matching
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        # Optionally redact IPs and hostnames (for public logs/sharing)
        if aggressive:
            for category in ['ip', 'hostname']:
                patterns = SensitiveDataProtector.SENSITIVE_PATTERNS.get(category, [])
                replacement = SensitiveDataProtector.REPLACEMENTS.get(category, '[REDACTED]')
                
                for pattern in patterns:
                    sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def sanitize_command(command: str) -> str:
        """Sanitize command for safe logging.
        
        Args:
            command: Command to sanitize
            
        Returns:
            Sanitized command
        """
        # Commands are generally safe, but check for inline passwords
        return SensitiveDataProtector.sanitize_for_logging(command, aggressive=False)
    
    @staticmethod
    def sanitize_output(output: str, max_length: int = 1000) -> str:
        """Sanitize command output for safe logging.
        
        Args:
            output: Output to sanitize
            max_length: Maximum length to log (0 = no limit)
            
        Returns:
            Sanitized output, possibly truncated
        """
        # Sanitize sensitive data
        sanitized = SensitiveDataProtector.sanitize_for_logging(output, aggressive=False)
        
        # Truncate if needed
        if max_length > 0 and len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + f"\n... [TRUNCATED: {len(output) - max_length} more chars]"
        
        return sanitized
    
    @staticmethod
    def sanitize_error(error: str) -> str:
        """Sanitize error message for safe display/logging.
        
        Args:
            error: Error message to sanitize
            
        Returns:
            Sanitized error message
        """
        return SensitiveDataProtector.sanitize_for_logging(error, aggressive=False)
    
    @staticmethod
    def sanitize_dict(data: dict[str, Any], aggressive: bool = False) -> dict[str, Any]:
        """Sanitize dictionary values recursively.
        
        Args:
            data: Dictionary to sanitize
            aggressive: If True, redact more aggressively
            
        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            # Check if key itself indicates sensitive data
            key_lower = key.lower()
            is_sensitive_key = any(
                sensitive in key_lower 
                for sensitive in ['password', 'passwd', 'pwd', 'secret', 'key', 'token', 'api']
            )
            
            if is_sensitive_key:
                # Completely redact sensitive keys
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, str):
                # Sanitize string values
                sanitized[key] = SensitiveDataProtector.sanitize_for_logging(value, aggressive)
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                sanitized[key] = SensitiveDataProtector.sanitize_dict(value, aggressive)
            elif isinstance(value, list):
                # Sanitize lists
                sanitized[key] = [
                    SensitiveDataProtector.sanitize_for_logging(str(item), aggressive) 
                    if isinstance(item, str) else item
                    for item in value
                ]
            else:
                # Keep non-string, non-dict values as-is
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def mask_password(password: str) -> str:
        """Mask password for display purposes.
        
        Args:
            password: Password to mask
            
        Returns:
            Masked password (e.g., "****")
        """
        if not password:
            return ""
        return "****" if len(password) <= 4 else "*" * len(password)
    
    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """Mask API key for display purposes.
        
        Args:
            api_key: API key to mask
            
        Returns:
            Masked API key (show first/last 4 chars)
        """
        if not api_key or len(api_key) < 8:
            return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"