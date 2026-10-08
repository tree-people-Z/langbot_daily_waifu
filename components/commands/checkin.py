from __future__ import annotations

from typing import AsyncGenerator

from langbot_plugin.api.definition.components.command.command import Command
from langbot_plugin.api.entities.builtin.command.context import CommandReturn, ExecuteContext

from .common import get_service, identity


class Checkin(Command):
    async def initialize(self):
        await super().initialize()

        @self.subcommand(name="", help="每日签到并领取积分", usage="签到", aliases=["打卡"])
        async def run(self, context: ExecuteContext) -> AsyncGenerator[CommandReturn, None]:
            service = get_service(self.plugin)
            sender, _, name, launcher_type, launcher_id = identity(context)
            scope = service.scope_id(launcher_type, launcher_id, service.config)
            yield CommandReturn(text=await service.checkin(sender, scope, name))
