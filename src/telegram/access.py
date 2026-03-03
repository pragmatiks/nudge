from telegram.ext import filters

from config import settings


class OwnerFilter(filters.MessageFilter):
    """Only allows messages from the configured owner."""

    def filter(self, message) -> bool:
        return message.from_user is not None and message.from_user.id == settings.telegram_owner_id


owner_filter = OwnerFilter()
