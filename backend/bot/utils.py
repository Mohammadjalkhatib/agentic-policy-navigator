import os
import time
from typing import Dict, Any, Optional
from telegram import Update, Message
from telegram.ext import ContextTypes
from pathlib import Path

# load settings
from config.settings import SECURITY, DOCUMENT_PROCESSING, TELEGRAM


def is_authorized_user(update: Update) -> bool:
    """Return True if the user is allowed."""
    user_id = update.effective_user.id
    authorized_ids = SECURITY["AUTHORIZED_USER_IDS"]

    # empty list = allow all
    if not authorized_ids:
        return True

    return user_id in authorized_ids


def format_response(
    status: str, message: str, details: Optional[Dict[str, Any]] = None
) -> str:
    """Return a user-facing message."""
    if status == "success":
        file_name = Path(details.get("Path", "")).name
        return (
            f"Document '{file_name}' has been successfully uploaded and indexed.\n"
            "You can now ask questions about this document. For example:\n"
            "- What is the main topic of this document?\n"
            "- Can you summarize the key points?\n"
            "- What are the main requirements mentioned?"
        )
    elif status == "error":
        return f"Error: {message}"
    elif status == "skipped":
        return "This document has already been uploaded and indexed. You can ask questions about it."
    else:
        response = f"{status.upper()}: {message}"
        if details:
            response += "\n\nDetails:"
            for key, value in details.items():
                response += f"\n- {key}: {value}"
        return response


def truncate_message(
    text: str, max_length: int = SECURITY["MAX_MESSAGE_LENGTH"]
) -> str:
    """Shorten text to max_length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def get_file_extension(file_name: str) -> str:
    """Return file extension."""
    return os.path.splitext(file_name)[1].lower()


def is_supported_file(file_name: str) -> bool:
    """Check if extension is supported."""
    extension = get_file_extension(file_name)
    return extension in TELEGRAM["SUPPORTED_FILE_TYPES"]


def get_user_info(update: Update) -> str:
    """Format user info for logs."""
    user = update.effective_user
    return (
        f"User {user.id} (@{user.username}) - {user.first_name} {user.last_name or ''}"
    )
