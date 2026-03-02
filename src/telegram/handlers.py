import logging

from telegram import Update
from telegram.ext import Application, ContextTypes

from src.agent.client import AgentClient

logger = logging.getLogger(__name__)

# Module-level agent client, initialized on first use
_agent: AgentClient | None = None


def _get_agent() -> AgentClient:
    global _agent
    if _agent is None:
        _agent = AgentClient()
    return _agent


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages by forwarding to Claude."""
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    logger.info("Message from owner (chat %s): %s", chat_id, user_text[:80])

    # Show typing indicator while Claude thinks
    await update.message.chat.send_action("typing")

    try:
        response = await _get_agent().send_message(user_text)
        await update.message.reply_text(
            response,
            parse_mode="Markdown",
        )
    except Exception:
        logger.exception("Error processing message")
        await update.message.reply_text(
            "Something went wrong. Check the logs.",
        )


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text("Hey! I'm Nudge, your personal assistant. What can I help with?")


async def shutdown_agent(app: Application) -> None:
    """Clean up the agent client on bot shutdown."""
    global _agent
    if _agent is not None:
        await _agent.close()
        _agent = None
