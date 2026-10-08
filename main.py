"""LangBot entry point for the daily check-in and waifu plugin."""

from langbot_plugin.api.definition.plugin import BasePlugin
from core.service import DailyService


class DailyWaifuPlugin(BasePlugin):
    """Plugin lifecycle entry point."""

    async def initialize(self):
        self._daily_waifu_service = DailyService(self.get_config() or {})
