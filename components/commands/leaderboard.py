from __future__ import annotations

from typing import AsyncGenerator

from langbot_plugin.api.definition.components.command.command import Command
from langbot_plugin.api.entities.builtin.command.context import CommandReturn, ExecuteContext

from .common import get_service, identity


class Leaderboard(Command):
    async def initialize(self):
        await super().initialize()

        @self.subcommand(name="", help="查看积分排行榜", usage="排行榜", aliases=["排行", "积分排行"])
        async def run(self, context: ExecuteContext) -> AsyncGenerator[CommandReturn, None]:
            service = get_service(self.plugin)
            _, _, _, launcher_type, launcher_id = identity(context)
            scope = service.scope_id(launcher_type, launcher_id, service.config)
            yield CommandReturn(text=await service.leaderboard(scope))
