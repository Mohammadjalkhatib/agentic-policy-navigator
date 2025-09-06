import os
import time
import logging
import asyncio
from telegram.ext import Application
from bot.handlers import setup_handlers
from config.secrets import TELEGRAM_BOT_TOKEN
from config.settings import SECURITY
from document.indexer import get_or_create_index
from document.default_data import DefaultDataLoader

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check environment settings."""
    # Check API key
    if not os.environ.get("AIxPLAIN_API_KEY"):
        raise EnvironmentError("AIxPLAIN_API_KEY is not set in environment variables")

    # Check bot token
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set correctly")

    # Check index exists
    try:
        index = get_or_create_index()
        print(f"Index verified: {index.name} (ID: {index.id})")
    except Exception as e:
        logger.error(f"Failed to access index: {str(e)}", exc_info=True)
        raise

    # Load default content
    default_loader = DefaultDataLoader()
    if not default_loader.load_default_content():
        logger.warning("Failed to load default content")
    else:
        logger.info("Default content loaded successfully")


def main():
    """Main entry point for the system."""
    try:
        # Check environment settings
        check_environment()

        # Create Telegram application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Setup handlers
        setup_handlers(application)

        # Start the bot
        print("Starting Telegram Knowledge Bot...")
        application.run_polling()

    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}", exc_info=True)
        print(f"Failed to start bot: {str(e)}")
        print("Please verify:")
        print("1. Telegram token validity")
        print("2. aiXplain API key validity")
        print("3. Internet connection availability")


if __name__ == "__main__":
    main()