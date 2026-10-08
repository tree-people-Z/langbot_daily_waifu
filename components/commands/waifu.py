from __future__ import annotations

from typing import AsyncGenerator

from langbot_plugin.api.definition.components.command.command import Command
from langbot_plugin.api.entities.builtin.command.context import CommandReturn, ExecuteContext

from .common import command_return, get_service, identity


class Waifu(Command):
    async def initialize(self):
        await super().initialize()

        @self.subcommand(name="", help="抽取今日老婆", usage="老婆", aliases=["今日老婆", "每日老婆"])
        async def draw(self, context: ExecuteContext) -> AsyncGenerator[CommandReturn, None]:
            service = get_service(self.plugin)
            sender, group, name, _, _ = identity(context)
            result = await service.wife(sender, group, name)
            yield command_return(result)

