"""Shared command helpers."""

import base64
import re
from pathlib import Path

from core.service import DailyService
from langbot_plugin.api.entities.builtin.command.context import CommandReturn


def get_service(plugin) -> DailyService:
    service = getattr(plugin, "_daily_waifu_service", None)
    if service is None:
        service = DailyService(plugin.get_config() or {})
        plugin._daily_waifu_service = service
    return service


def identity(context):
    session = context.session
    sender_id = str(session.sender_id or session.launcher_id)
    sender_name = str(getattr(session, "sender_name", "") or sender_id)
    launcher_type = getattr(session.launcher_type, "value", session.launcher_type)
    group_id = str(session.launcher_id) if launcher_type == "group" else ""
    return sender_id, group_id, sender_name, launcher_type, str(session.launcher_id)


def command_return(result: dict) -> CommandReturn:
    """Build a transport-safe response without Runtime file-transfer keys."""
    image_base64 = None
    image_path = result.get("image")
    if image_path:
        try:
            image_base64 = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        except (OSError, TypeError, ValueError):
            image_base64 = None
    return CommandReturn(text=plain_text(result.get("text", "")), image_base64=image_base64)


def plain_text(text: str) -> str:
    """Remove Markdown control syntax for chat adapters that send plain text."""
    text = re.sub(r"^#{1,6}\s*", "", str(text), flags=re.MULTILINE)
    text = text.replace("**", "")
    text = re.sub(r"^---$", "", text, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
