"""Shared command helpers."""

from core.service import DailyService


def get_service(plugin) -> DailyService:
    service = getattr(plugin, "_daily_waifu_service", None)
    if service is None:
        service = DailyService(plugin.get_config() or {})
        plugin._daily_waifu_service = service
    return service


def identity(context):
    session = context.session
    sender_id = str(session.sender_id or session.launcher_id)
    sender_name = sender_id
    launcher_type = getattr(session.launcher_type, "value", session.launcher_type)
    group_id = str(session.launcher_id) if launcher_type == "group" else ""
    return sender_id, group_id, sender_name, launcher_type, str(session.launcher_id)
