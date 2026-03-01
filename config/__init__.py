from functools import lru_cache

from config.settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Lazy proxy — accessed as `settings.X` but only constructed on first attribute access
class _SettingsProxy:
    def __getattr__(self, name: str):
        return getattr(get_settings(), name)


settings = _SettingsProxy()

__all__ = ["settings", "get_settings"]
