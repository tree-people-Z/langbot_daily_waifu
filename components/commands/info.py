from __future__ import annotations

from typing import AsyncGenerator

from langbot_plugin.api.definition.components.command.command import Command
from langbot_plugin.api.entities.builtin.command.context import CommandReturn, ExecuteContext

from .common import get_service, identity


class Info(Command):
    async def initialize(self):
        await super().initialize()

        @self.subcommand(name="", help="查看积分、签到和今日老婆", usage="我的信息", aliases=["我的", "me"])
        async def run(self, context: ExecuteContext) -> AsyncGenerator[CommandReturn, None]:
            service = get_service(self.plugin)
            sender, group, name, launcher_type, launcher_id = identity(context)
            scope = service.scope_id(launcher_type, launcher_id, service.config)
            yield CommandReturn(text=await service.my_info(sender, scope, group, name))
