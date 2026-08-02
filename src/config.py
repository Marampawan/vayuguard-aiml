"""
Configuration loader for VayuGuard
Securely loads API keys and settings from environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# qBraid Quantum Cloud Platform Configuration
QBRAID_API_KEY = os.getenv('QBRAID_API_KEY', '')

# Validate critical configuration
def validate_config():
    """Validate that required configuration is present"""
    errors = []
    
    if not QBRAID_API_KEY:
        errors.append("QBRAID_API_KEY not set. Please set it in .env file or environment variables.")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(errors))
    
    return True

# Optional: Auto-validate on import (comment out if you want lazy validation)
# validate_config()