import json
import os
from datetime import datetime

import flet as ft
import httpx


class SyncService:
    _PENDING_KEY = "wf_pending_dates"
    _CHANGE_KEY_PREFIX = "wf_change_"
    _API_TOKEN_KEY = "wf_api_token"
    _API_URL_KEY = "wf_api_url"
    _LAST_SYNC_KEY = "wf_last_sync"

    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db

    def _run_task(self, handler, *args, **kwargs):
        if hasattr(self.page, "run_task"):
            self.page.run_task(handler, *args, **kwargs)
            return
        try:
            import asyncio

            asyncio.run(handler(*args, **kwargs))
        except Exception:
            pass

    def store_snapshot(self, workout_date: str, content: str, notes: str) -> None:
        async def _task():
            prefs = ft.SharedPreferences()
            payload = json.dumps(
                {"date": workout_date, "content": content, "notes": notes},
                ensure_ascii=False,
            )
            await prefs.set(f"{self._CHANGE_KEY_PREFIX}{workout_date}", payload)

        self._run_task(_task)

    def remove_snapshot(self, workout_date: str) -> None:
        async def _task():
            prefs = ft.SharedPreferences()
            await prefs.remove(f"{self._CHANGE_KEY_PREFIX}{workout_date}")

        self._run_task(_task)

    def clear_pending(self, workout_date: str) -> None:
        async def _task():
            prefs = ft.SharedPreferences()
            await prefs.remove(f"{self._CHANGE_KEY_PREFIX}{workout_date}")
            pending = await prefs.get(self._PENDING_KEY)
            if not isinstance(pending, list) or not pending:
                return
            if workout_date in pending:
                pending = [d for d in pending if d != workout_date]
                if pending:
                    await prefs.set(self._PENDING_KEY, pending)
                else:
                    await prefs.remove(self._PENDING_KEY)

        self._run_task(_task)

    def queue_upsert(self, workout_date: str, content: str, notes: str) -> None:
        async def _task():
            prefs = ft.SharedPreferences()
            payload = json.dumps(
                {
                    "action": "upsert",
                    "date": workout_date,
                    "content": content,
                    "notes": notes,
                    "ts": datetime.now().isoformat(timespec="seconds"),
                },
                ensure_ascii=False,
            )
            await prefs.set(f"{self._CHANGE_KEY_PREFIX}{workout_date}", payload)
            pending = await prefs.get(self._PENDING_KEY)
            if not isinstance(pending, list):
                pending = []
            if workout_date not in pending:
                pending.append(workout_date)
            await prefs.set(self._PENDING_KEY, pending)

        self._run_task(_task)

    def queue_delete(self, workout_date: str) -> None:
        async def _task():
            prefs = ft.SharedPreferences()
            payload = json.dumps(
                {
                    "action": "delete",
                    "date": workout_date,
                    "ts": datetime.now().isoformat(timespec="seconds"),
                },
                ensure_ascii=False,
            )
            await prefs.set(f"{self._CHANGE_KEY_PREFIX}{workout_date}", payload)
            pending = await prefs.get(self._PENDING_KEY)
            if not isinstance(pending, list):
                pending = []
            if workout_date not in pending:
                pending.append(workout_date)
            await prefs.set(self._PENDING_KEY, pending)

        self._run_task(_task)

    async def _get_api_config(self, prefs):
        api_url = await prefs.get(self._API_URL_KEY)
        if not api_url or not isinstance(api_url, str):
            api_url = "https://serjsamotoyloff.ru"
        api_token = await prefs.get(self._API_TOKEN_KEY)
        if not api_token or not isinstance(api_token, str):
            api_token = ""
        return api_url.rstrip("/"), api_token.strip()

    def flush_pending(self) -> None:
        async def _task():
            prefs = ft.SharedPreferences()
            pending = await prefs.get(self._PENDING_KEY)
            if not isinstance(pending, list) or not pending:
                return

            user_id = getattr(self.page, "_wf_user_id", None) or "default"
            api_url, api_token = await self._get_api_config(prefs)

            if not api_token:
                return

            remaining: list[str] = []
            for workout_date in pending:
                raw = await prefs.get(f"{self._CHANGE_KEY_PREFIX}{workout_date}")
                if not isinstance(raw, str) or not raw.strip():
                    continue
                try:
                    data = json.loads(raw)
                except Exception:
                    remaining.append(workout_date)
                    continue

                action = str(data.get("action") or "upsert")
                try:
                    await self._sync_one_to_api(
                        api_url=api_url,
                        api_token=api_token,
                        action=action,
                        user_id=user_id,
                        date=data.get("date", workout_date),
                        content=data.get("content", ""),
                        notes=data.get("notes", ""),
                    )
                    await prefs.remove(f"{self._CHANGE_KEY_PREFIX}{workout_date}")
                except Exception:
                    remaining.append(workout_date)

            if remaining:
                await prefs.set(self._PENDING_KEY, remaining)
            else:
                await prefs.remove(self._PENDING_KEY)

        self._run_task(_task)

    async def _sync_one_to_api(self, api_url: str, api_token: str, action: str, user_id: str, date: str, content: str, notes: str):
        headers = {"X-API-Token": api_token}
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "delete":
                response = await client.delete(
                    f"{api_url}/api/workouts/{date}",
                    headers=headers,
                    params={"user_id": user_id}
                )
                response.raise_for_status()
            else:
                response = await client.put(
                    f"{api_url}/api/workouts/{date}",
                    headers=headers,
                    json={"content": content, "notes": notes},
                    params={"user_id": user_id}
                )
                response.raise_for_status()

    def sync_from_api(self, on_complete=None) -> None:
        async def _task():
            prefs = ft.SharedPreferences()
            user_id = getattr(self.page, "_wf_user_id", None) or "default"
            api_url, api_token = await self._get_api_config(prefs)
            if not api_token:
                return

            headers = {"X-API-Token": api_token}
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{api_url}/api/workouts",
                    headers=headers,
                    params={"user_id": user_id}
                )
                response.raise_for_status()
                data = response.json()

            items = data.get("items", [])
            for item in items:
                try:
                    if item.get("content") or item.get("notes"):
                        self.db.upsert_workout_by_date(
                            date=item["date"],
                            content=item.get("content", ""),
                            notes=item.get("notes", ""),
                            user_id=user_id
                        )
                    else:
                        self.db.delete_workouts_by_date(
                            date=item["date"],
                            user_id=user_id
                        )
                except Exception:
                    pass

            try:
                await prefs.set(self._LAST_SYNC_KEY, datetime.now().isoformat())
            except Exception:
                pass

            if on_complete:
                on_complete()

        self._run_task(_task)

    async def set_api_credentials(self, api_url: str, api_token: str) -> None:
        prefs = ft.SharedPreferences()
        if api_url:
            await prefs.set(self._API_URL_KEY, api_url.strip())
        if api_token:
            await prefs.set(self._API_TOKEN_KEY, api_token.strip())

    async def get_last_sync(self) -> str:
        try:
            prefs = ft.SharedPreferences()
            last = await prefs.get(self._LAST_SYNC_KEY)
            if isinstance(last, str) and last:
                return last
        except Exception:
            pass
        return ""
