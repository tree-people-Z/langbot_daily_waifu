from __future__ import annotations

from typing import AsyncGenerator

from langbot_plugin.api.definition.components.command.command import Command
from langbot_plugin.api.entities.builtin.command.context import CommandReturn, ExecuteContext
from langbot_plugin.api.entities.builtin.platform.message import Image, MessageChain, Plain

from .common import get_service, identity


class Waifu(Command):
    async def initialize(self):
        await super().initialize()

        @self.subcommand(name="", help="抽取今日老婆", usage="老婆", aliases=["今日老婆", "每日老婆"])
        async def draw(self, context: ExecuteContext) -> AsyncGenerator[CommandReturn, None]:
            service = get_service(self.plugin)
            sender, group, name, _, _ = identity(context)
            result = await service.wife(sender, group, name)
            if result.get("image"):
                await context.reply(MessageChain([Image(path=result["image"]), Plain(text="\n" + result["text"])]))
            else:
                await context.reply(MessageChain([Plain(text=result["text"])]))
            if False:
                yield CommandReturn()

