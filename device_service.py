import uuid

import flet as ft


class DeviceService:
    KEY = "wf_device_id"

    def __init__(self, page: ft.Page):
        self.page = page

    async def get_or_create_device_id(self) -> str:
        prefs = ft.SharedPreferences()
        existing = await prefs.get(self.KEY)
        if isinstance(existing, str) and existing.strip():
            device_id = existing.strip()
        else:
            device_id = str(uuid.uuid4())
            await prefs.set(self.KEY, device_id)
        try:
            setattr(self.page, "_wf_device_id", device_id)
        except Exception:
            pass
        return device_id

