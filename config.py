"""
Configuration management for Portfolio Rebalancer
"""
import json
import os
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / '.rebalancer_config.json'


def load_config():
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def get_groq_api_key():
    """Get Groq API key from config."""
    config = load_config()
    return config.get('groq_api_key', '')


def set_groq_api_key(api_key):
    """Save Groq API key to config."""
    config = load_config()
    config['groq_api_key'] = api_key
    return save_config(config)


def clear_groq_api_key():
    """Remove Groq API key from config."""
    config = load_config()
    if 'groq_api_key' in config:
        del config['groq_api_key']
        return save_config(config)
    return True
