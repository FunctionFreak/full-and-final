# browser-assistant/config/env.py
import os
from dotenv import load_dotenv
from pathlib import Path

def load_env_vars(env_file=".env"):
    base_path = Path(__file__).parent.parent  # This points to the project root.
    env_path = base_path / env_file
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"Environment variables loaded from {env_path}")
    else:
        print(f".env file not found at {env_path}")

# Load environment variables immediately when this module is imported.
load_env_vars()
