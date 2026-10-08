from __future__ import annotations

from typing import AsyncGenerator

from langbot_plugin.api.definition.components.command.command import Command
from langbot_plugin.api.entities.builtin.command.context import CommandReturn, ExecuteContext

from .common import command_return, get_service, identity


class ChangeWife(Command):
    async def initialize(self):
        await super().initialize()

        @self.subcommand(name="", help="消耗积分重新抽取今日老婆", usage="换老婆", aliases=["换"])
        async def run(self, context: ExecuteContext) -> AsyncGenerator[CommandReturn, None]:
            service = get_service(self.plugin)
            sender, group, name, launcher_type, launcher_id = identity(context)
            scope = service.scope_id(launcher_type, launcher_id, service.config)
            result = await service.change_wife(sender, scope, group, name)
            yield command_return(result)
