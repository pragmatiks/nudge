import logging

from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

NUDGE_DELIVERY_PROMPT = """\
[INTERNAL — NUDGE DELIVERY]
You have a pending reminder for the owner. Compose a brief, natural follow-up message.

Nudge: {about}
Context: {context}

Be conversational, not robotic. Don't say "reminder" or "nudge" — just bring it up naturally, \
like a thoughtful assistant checking in. Keep it to 1-2 sentences."""

DAILY_BRIEFING_PROMPT = """\
[INTERNAL — DAILY BRIEFING]
Good morning! Compose a brief daily briefing for the owner.

Check their Todoist tasks for today and any overdue items. Also search your memory for any \
relevant context about ongoing projects or commitments.

Format: Start with a friendly greeting, then list today's priorities. Keep it concise — \
bullet points are fine. If there's nothing urgent, say so briefly."""


async def check_nudges(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Repeating job: check for due nudges and deliver them."""
    coordinator = context.bot_data["coordinator"]
    store = context.bot_data["nudge_store"]
    evaluator = context.bot_data["evaluator"]
    chat_id = context.bot_data["owner_chat_id"]

    due = store.get_due()
    if not due:
        return

    for nudge in due:
        allowed, reason = evaluator.should_deliver()
        if not allowed:
            logger.info("Nudge %s suppressed: %s", nudge.id, reason)
            continue

        try:
            prompt = NUDGE_DELIVERY_PROMPT.format(about=nudge.about, context=nudge.context)
            sent = False

            async def _send(text):
                nonlocal sent
                await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
                sent = True

            response = await coordinator.process_internal(prompt, on_text=_send)
            if not sent:
                await context.bot.send_message(chat_id=chat_id, text=response, parse_mode="Markdown")
            store.mark_sent(nudge.id)
            logger.info("Delivered nudge %s", nudge.id)
        except Exception:
            logger.exception("Failed to deliver nudge %s", nudge.id)


async def daily_briefing(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Daily job: send morning briefing and clean up old nudges."""
    coordinator = context.bot_data["coordinator"]
    store = context.bot_data["nudge_store"]
    chat_id = context.bot_data["owner_chat_id"]

    store.cleanup_old()

    try:
        sent = False

        async def _send(text):
            nonlocal sent
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
            sent = True

        response = await coordinator.process_internal(DAILY_BRIEFING_PROMPT, on_text=_send)
        if not sent:
            await context.bot.send_message(chat_id=chat_id, text=response, parse_mode="Markdown")
        logger.info("Daily briefing sent")
    except Exception:
        logger.exception("Failed to send daily briefing")


async def task_checkin(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Self-scheduling job: ask the task monitor to assess tasks, deliver if needed."""
    monitor = context.bot_data["monitor"]
    coordinator = context.bot_data["coordinator"]
    evaluator = context.bot_data["evaluator"]
    chat_id = context.bot_data["owner_chat_id"]

    next_minutes = 30  # default fallback

    try:
        result = await monitor.check()
        next_minutes = result.next_check_minutes

        if result.should_check_in:
            allowed, reason = evaluator.should_deliver()
            if allowed:
                prompt = f"[INTERNAL — TASK CHECK-IN]\n{result.prompt}"
                sent = False

                async def _send(text):
                    nonlocal sent
                    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
                    sent = True

                response = await coordinator.process_internal(prompt, on_text=_send)
                if not sent:
                    await context.bot.send_message(chat_id=chat_id, text=response, parse_mode="Markdown")
                logger.info("Task check-in delivered")
            else:
                logger.info("Task check-in suppressed: %s", reason)
    except Exception:
        logger.exception("Task check-in failed")
    finally:
        context.job_queue.run_once(task_checkin, when=next_minutes * 60, name="task_checkin")
        logger.info("Next task check-in in %d minutes", next_minutes)
