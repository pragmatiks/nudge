import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import settings
from src.telegram.access import owner_filter
from src.telegram.handlers import handle_message, handle_start

logger = logging.getLogger(__name__)


def create_app() -> Application:
    """Build and configure the Telegram bot application."""
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )

    # Commands — owner only
    app.add_handler(CommandHandler("start", handle_start, filters=owner_filter))

    # Text messages — owner only
    app.add_handler(MessageHandler(owner_filter & filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Telegram bot configured (owner_id=%s)", settings.telegram_owner_id)
    return app
