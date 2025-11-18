#!/usr/bin/env python3
"""
Secure credential helper for the AI Network Agent.

This script provides a secure way to manage credentials by:
1. Generating encrypted environment files
2. Converting hardcoded inventory credentials to use environment variables
3. Providing guidance on secure credential storage
"""

import os
import sys
from pathlib import Path
import yaml
import json
from getpass import getpass
import base64
from cryptography.fernet import Fernet

def generate_key():
    """Generate a key for encryption/decryption."""
    return Fernet.generate_key()

def encrypt_data(data, key):
    """Encrypt data using the provided key."""
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_data(encrypted_data, key):
    """Decrypt data using the provided key."""
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()

def create_secure_inventory():
    """Create an encrypted inventory file or update the existing one to use environment variables."""
    print("Creating secure inventory configuration...")
    
    # Load existing inventory
    try:
        with open("inventory.yaml", "r") as f:
            inventory_data = yaml.safe_load(f)
    except FileNotFoundError:
        print("No inventory.yaml file found. Creating example inventory...")
        inventory_data = {
            "devices": [
                {
                    "name": "D1",
                    "hostname": "192.168.121.101",
                    "username": "${DEVICE_USERNAME_D1}",
                    "password": "${DEVICE_PASSWORD_D1}",
                    "device_type": "cisco_ios",
                    "role": "distribution",
                    "connection_protocol": "netmiko"
                }
            ]
        }
    
    # Update inventory to use environment variables
    for device in inventory_data.get("devices", []):
        device["username"] = f"${{DEVICE_USERNAME_{device['name']}}}"
        device["password"] = f"${{DEVICE_PASSWORD_{device['name']}}}"
    
    # Save updated inventory
    with open("secure_inventory.yaml", "w") as f:
        yaml.dump(inventory_data, f, default_flow_style=False)
    
    print("Updated inventory to use environment variables in secure_inventory.yaml")
    print("Remember to set these environment variables before running the application.")

def create_secure_env():
    """Create a secure .env file with encrypted values."""
    print("\nCreating secure .env file...")
    
    # Get sensitive values
    groq_api_key = getpass("Enter your GROQ API key (will not be displayed): ")
    mistral_api_key = getpass("Enter your Mistral API key (will not be displayed, press Enter to skip): ") or None
    
    # Generate encryption key
    key = generate_key()
    
    # Create encrypted environment file
    env_content = {
        "GROQ_API_KEY": base64.b64encode(encrypt_data(groq_api_key, key)).decode(),
    }
    
    if mistral_api_key:
        env_content["MISTRAL_API_KEY"] = base64.b64encode(encrypt_data(mistral_api_key, key)).decode()
    
    # Save encrypted values to .env file
    with open(".env.encrypted", "w") as f:
        json.dump(env_content, f, indent=2)
    
    # Save key separately (in a real application, this should be stored more securely)
    with open(".env.key", "wb") as f:
        f.write(key)
    
    print("\nEncrypted environment file created as .env.encrypted")
    print("Encryption key saved as .env.key")
    print("\nTo use these values in your application, you'll need to:")
    print("1. Create a custom configuration loader that decrypts these values")
    print("2. Add '.env.encrypted' and '.env.key' to your .gitignore file")
    print("3. Store the key in a secure location (preferably external)")

def update_config_for_encryption():
    """Update the config module to handle encrypted credentials."""
    print("\nYou should update src/core/config.py to handle encrypted credentials.")
    print("Here's an example of how to modify the Settings class:")
    
    print("""
from pydantic_settings import BaseSettings
import json
import base64
from cryptography.fernet import Fernet

class Settings(BaseSettings):
    inventory_file: str = "inventory.yaml"
    spacy_model: str = "en_core_web_sm"
    groq_model_name: str = "llama-3.1-8b-instant"
    groq_temperature: float = 0.7
    state_database_file: str = "agent_state.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def get_groq_api_key(self):
        # Try to get decrypted key from encrypted file
        try:
            with open(".env.encrypted", "r") as f:
                encrypted_data = json.load(f)
            with open(".env.key", "rb") as f:
                key = f.read()
            
            encrypted_key = base64.b64decode(encrypted_data["GROQ_API_KEY"])
            return Fernet(key).decrypt(encrypted_key).decode()
        except FileNotFoundError:
            # Fall back to environment variable
            import os
            return os.getenv("GROQ_API_KEY", self.groq_api_key)

# Create a single, importable instance of the settings
settings = Settings()
    """)

def main():
    print("AI Network Agent - Secure Credential Setup Tool")
    print("=" * 50)
    print("This tool helps you securely manage credentials for the network agent.")
    print()
    
    while True:
        print("\nOptions:")
        print("1. Create secure inventory (convert hardcoded credentials to environment variables)")
        print("2. Create encrypted .env file for API keys")
        print("3. Show example config changes for encrypted credentials")
        print("4. Exit")
        
        choice = input("\nSelect an option (1-4): ").strip()
        
        if choice == "1":
            create_secure_inventory()
        elif choice == "2":
            create_secure_env()
        elif choice == "3":
            update_config_for_encryption()
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please select 1-4.")
    
    print("\nSecurity best practices:")
    print("- Never commit .env files or encryption keys to version control")
    print("- Use proper access controls for credential files")
    print("- Consider using a secrets management service (AWS Secrets Manager, HashiCorp Vault, etc.)")
    print("- Regularly rotate credentials")

if __name__ == "__main__":
    # Check if required packages are available
    try:
        import yaml
        import cryptography
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please install required packages: pip install pyyaml cryptography")
        sys.exit(1)
    
    main()