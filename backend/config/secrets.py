"""Secrets loader - do NOT store secrets in this file in source control.

Reads values from environment variables. For local development create a
`.env` file (see `.env.example`) and add `.env` to `.gitignore`.
"""

from dotenv import load_dotenv
import os

load_dotenv()

# Required credentials (set these in your environment or in a local .env file)
AIxPLAIN_API_KEY = os.getenv("AIxPLAIN_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Optional defaults (IDs) can be provided via env vars.
DEFAULT_INDEX_ID = os.getenv("DEFAULT_INDEX_ID", "")
DEFAULT_AGENT_ID = os.getenv("DEFAULT_AGENT_ID", "")
