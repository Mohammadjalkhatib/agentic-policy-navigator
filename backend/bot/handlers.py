import os
import time
from typing import Dict, Any
from telegram import Update, Message
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ChatMemberHandler,
)
from config.settings import TELEGRAM, SECURITY
from bot.commands import (
    start_command,
    help_command,
    status_command,
    session_status,
    add_document,
)
from bot.utils import is_authorized_user, is_supported_file, get_file_extension
from document.processor import DocumentProcessor
from aixplain.factories import AgentFactory
from config.secrets import DEFAULT_AGENT_ID, DEFAULT_INDEX_ID

# User session IDs
user_sessions = {}


async def handle_text_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text queries with session support."""
    if not is_authorized_user(update):
        await update.message.reply_text(
            "Sorry, you are not authorized to use this bot."
        )
        return

    user_id = update.effective_user.id
    query = update.message.text
    user_info = f"User {user_id}"

    print(f"{user_info} - Received question: {query}")

    try:
        # typing action
        await update.message.chat.send_action("typing")

        # load agent
        try:
            agent = AgentFactory.get(DEFAULT_AGENT_ID)
        except Exception as e:
            print(f"Error getting Agent: {str(e)}")
            await update.message.reply_text(
                "Error connecting to Agent. Check Agent ID."
            )
            return

        # get session
        session_id = user_sessions.get(user_id)

        # run agent
        try:
            if session_id:
                print(
                    f"{user_info} - Using session_id: {session_id} to continue conversation"
                )
                response = agent.run(query=query, session_id=session_id)
            else:
                print(f"{user_info} - Starting new conversation without session_id")
                response = agent.run(query=query)

            # extract answer
            if hasattr(response, "data"):
                if isinstance(response.data, str):
                    # handle string data
                    import ast

                    try:
                        data_dict = ast.literal_eval(response.data)
                        answer = data_dict.get("output", "")
                    except:
                        answer = response.data
                else:
                    # handle object data
                    answer = getattr(response.data, "output", "")
            else:
                answer = "Sorry, I couldn't understand the answer"

            # reply with answer
            await update.message.reply_text(answer)

            # update session
            try:
                if hasattr(response, "data"):
                    session_id = None
                    if isinstance(response.data, str):
                        try:
                            data_dict = ast.literal_eval(response.data)
                            session_id = (data_dict.get("execution_stats") or {}).get(
                                "session_id"
                            )
                        except:
                            pass
                    else:
                        session_id = (
                            getattr(response.data, "execution_stats", {}) or {}
                        ).get("session_id")

                    if session_id:
                        user_sessions[user_id] = session_id
                        print(f"{user_info} - Session ID updated: {session_id}")
            except Exception as e:
                print(f"Error updating session_id: {str(e)}")

            print(f"{user_info} - Question answered")

        except Exception as e:
            print(f"Error running Agent: {str(e)}")
            await update.message.reply_text("Error processing question.")
            return

    except Exception as e:
        error_msg = f"Error processing question: {str(e)}"
        await update.message.reply_text(error_msg)
        print(f"{user_info} - Error processing question: {str(e)}")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded documents."""
    if not is_authorized_user(update):
        await update.message.reply_text(
            "Sorry, you are not authorized to use this bot."
        )
        return

    user_id = update.effective_user.id
    user_info = f"User {user_id}"

    # get message & document
    message: Message = update.message
    document = message.document

    if not document:
        return

    file_name = document.file_name
    file_id = document.file_id

    print(f"{user_info} - Receiving file: {file_name} (ID: {file_id})")

    # check file type
    if not is_supported_file(file_name):
        await update.message.reply_text(
            f"Unsupported file type: {get_file_extension(file_name)}\n"
            f"Supported types: {', '.join(TELEGRAM['SUPPORTED_FILE_TYPES'])}"
        )
        return

    # check size
    file_size_mb = document.file_size / (1024 * 1024)
    if file_size_mb > TELEGRAM["MAX_FILE_SIZE_MB"]:
        await update.message.reply_text(
            f"File size exceeds maximum allowed size ({TELEGRAM['MAX_FILE_SIZE_MB']} MB)"
        )
        return

    try:
        # download & save
        file = await context.bot.get_file(file_id)
        processor = DocumentProcessor()
        file_path = processor.save_temp_file(
            await file.download_as_bytearray(), file_name
        )

        # process & index
        await add_document(update, context, file_path)

    except Exception as e:
        error_msg = f"Failed to download or process file: {str(e)}"
        await update.message.reply_text(error_msg)
        print(f"{user_info} - Error downloading file: {str(e)}")


async def chat_member_updated(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot added to a group/channel handler."""
    if update.chat_member and update.chat_member.new_chat_member:
        new_member = update.chat_member.new_chat_member
        if new_member.user.id == context.bot.id and new_member.status in [
            "member",
            "administrator",
        ]:
            # bot added
            welcome_message = (
                "*Welcome to Knowledge Bot!*\n\n"
                'You can now ask any question about the document "Virginia\'s New Consumer Data Protection Act", '
                "or about any executive order you're interested in.\n\n"
                "You can also upload new documents and ask questions about them directly.\n\n"
                "Just ask your question, and I'll help you find the answer from the available documents!\n\n"
                "Available commands:\n"
                "/help - Show help information\n"
                "/search - Search in documents\n"
                "/add - Upload new document\n"
                "/status - Check system status"
            )
            await context.bot.send_message(
                chat_id=update.chat_member.chat.id,
                text=welcome_message,
                parse_mode="Markdown",
            )


def setup_handlers(application):
    """Register handlers."""
    # Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("session", session_status))

    # Handle text (questions)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_query)
    )

    # Handle files (documents)
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Add chat member handler for welcome message
    application.add_handler(ChatMemberHandler(chat_member_updated))

    print("Bot handlers setup successfully")
