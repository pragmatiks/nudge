import logging

from telegram import Update
from telegram.ext import Application, ContextTypes

from src.coordinator import Coordinator

logger = logging.getLogger(__name__)

_coordinator: Coordinator | None = None


def set_coordinator(coordinator: Coordinator) -> None:
    global _coordinator
    _coordinator = coordinator


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages by forwarding to Claude."""
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    logger.info("Message from owner (chat %s): %s", chat_id, user_text[:80])

    await update.message.chat.send_action("typing")
    sent_any = False

    async def send_text(text: str) -> None:
        nonlocal sent_any
        await context.bot.send_message(chat_id, text, parse_mode="Markdown")
        await update.message.chat.send_action("typing")
        sent_any = True

    try:
        response = await _coordinator.process_message(user_text, on_text=send_text)
        if not sent_any:
            await update.message.reply_text(response, parse_mode="Markdown")
    except Exception:
        logger.exception("Error processing message")
        await update.message.reply_text("Something went wrong. Check the logs.")


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        "Hey! I'm Nudge, your personal assistant. What can I help with?"
    )


async def shutdown_agent(app: Application) -> None:
    """Clean up on bot shutdown."""
    pass
