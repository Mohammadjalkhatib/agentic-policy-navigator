from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import TELEGRAM, DOCUMENT_PROCESSING
from bot.utils import is_authorized_user, format_response, get_user_info
from document.indexer import get_or_create_index, process_and_upsert_document
from document.processor import DocumentProcessor
import os
import time
import logging

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command."""
    if not is_authorized_user(update):
        await update.message.reply_text(
            "Sorry, you are not authorized to use this bot."
        )
        return

    welcome_message = (
        "*Welcome to Knowledge Bot!*\n\n"
        'You can now ask any question about the document "Executive Order Authorizing the Implementation of Certain Sanctions Set Forth in the Countering America\'s Adversaries Through Sanctions Act", '
        "or about any executive order you're interested in.\n\n"
        "You can also upload new documents and ask questions about them directly.\n\n"
        "Just ask your question, and I'll help you find the answer from the available documents!\n\n"
        "Available commands:\n"
        "/help - Show help information\n"
        "/search - Search in documents\n"
        "/add - Upload new document\n"
        "/status - Check system status"
    )

    try:
        await update.message.reply_text(welcome_message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        await update.message.reply_text(
            "An error occurred while starting the bot. Please try again."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command."""
    if not is_authorized_user(update):
        await update.message.reply_text(
            "Sorry, you are not authorized to use this bot."
        )
        return

    help_message = (
        "Available Commands:\n\n"
        "/start - Start conversation with bot\n"
        "/help - Show this list\n"
        "/status - Show system status\n"
        "/session - Show current conversation session status\n"
        "/add - Add document to knowledge base (you can simply send the document)\n"
        "/search - Search in knowledge base (you can simply ask a question)\n\n"
        "Note: You can send documents or questions directly without using commands."
    )

    await update.message.reply_text(help_message)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system status."""
    if not is_authorized_user(update):
        await update.message.reply_text(
            "Sorry, you are not authorized to use this bot."
        )
        return

    try:
        # fetch index
        index = get_or_create_index()

        # collect info
        status_info = {
            "index_name": index.name,
            "index_id": index.id,
            "document_count": index.count(),
            "status": "active",
        }

        status_message = (
            "System Status:\n\n"
            f"• Knowledge Index: {status_info['index_name']} (ID: {status_info['index_id']})\n"
            f"• Document Count: {status_info['document_count']}\n"
            f"• Status: {status_info['status']}\n"
            f"• Settings: {DOCUMENT_PROCESSING['CHUNK_SIZE']} chars/chunk, {DOCUMENT_PROCESSING['CHUNK_OVERLAP']} overlap"
        )

        await update.message.reply_text(status_message)

    except Exception as e:
        error_message = format_response(
            "error", "Failed to get system status", {"Details": str(e)}
        )
        await update.message.reply_text(error_message)


user_sessions = {}


async def session_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show session status."""
    if not is_authorized_user(update):
        await update.message.reply_text(
            "Sorry, you are not authorized to use this bot."
        )
        return

    user_id = update.effective_user.id
    session_id = user_sessions.get(user_id, "No active session")

    status_message = (
        "Session Status:\n\n"
        f"• Session Status: {'Active' if user_id in user_sessions else 'Inactive'}\n"
        f"• session_id: {session_id}\n"
        f"• Questions in this session: {'Unknown' if session_id == 'No active session' else 'Depends on Agent'}"
    )

    await update.message.reply_text(status_message)


async def add_document(
    update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: str
):
    """Add document to index."""
    if not is_authorized_user(update):
        await update.message.reply_text(
            "Sorry, you are not authorized to use this bot."
        )
        return

    user_info = get_user_info(update)
    print(f"{user_info} - Starting document processing: {file_path}")

    try:
        # init processor
        processor = DocumentProcessor()

        # process file
        document_data = processor.process_file(file_path)

        if not document_data:
            await update.message.reply_text(
                "Failed to process document. Make sure the file is valid."
            )
            return

        # fetch index
        index = get_or_create_index()

        # upsert doc
        result = process_and_upsert_document(index, document_data)

        # build reply
        response = format_response(
            result["status"],
            result["message"],
            {
                "Path": result.get("file_path", "Not available"),
                "Size": f"{result.get('file_size', 0)} bytes",
                "Chunks": result.get("total_chunks", 0),
            },
        )

        await update.message.reply_text(response)
        print(f"{user_info} - Document processed successfully: {file_path}")

    except Exception as e:
        error_msg = format_response(
            "error", "Error processing document", {"Details": str(e)}
        )
        await update.message.reply_text(error_msg)
        print(f"{user_info} - Error processing document: {str(e)}")

    finally:
        # cleanup temp file
        if os.path.exists(file_path):
            os.remove(file_path)
