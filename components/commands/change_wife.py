from __future__ import annotations

from typing import AsyncGenerator

from langbot_plugin.api.definition.components.command.command import Command
from langbot_plugin.api.entities.builtin.command.context import CommandReturn, ExecuteContext
from langbot_plugin.api.entities.builtin.platform.message import Image, MessageChain, Plain

from .common import get_service, identity


class ChangeWife(Command):
    async def initialize(self):
        await super().initialize()

        @self.subcommand(name="", help="消耗积分重新抽取今日老婆", usage="换老婆", aliases=["换"])
        async def run(self, context: ExecuteContext) -> AsyncGenerator[CommandReturn, None]:
            service = get_service(self.plugin)
            sender, group, name, launcher_type, launcher_id = identity(context)
            scope = service.scope_id(launcher_type, launcher_id, service.config)
            result = await service.change_wife(sender, scope, group, name)
            if result.get("image"):
                await context.reply(
                    MessageChain([
                        Image(path=result["image"]),
                        Plain(text="\n" + result["text"]),
                    ])
                )
            else:
                await context.reply(MessageChain([Plain(text=result["text"])]))
            if False:
                yield CommandReturn()
