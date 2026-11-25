import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path


class SubscriptionService:
    TRIAL_DAYS = 21
    SUBSCRIPTION_DAYS = 30
    _TRIAL_WARNING_SHOWN_KEY = "trial_warning_day10_shown"

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = str(Path(__file__).with_name("workout_flow.db"))
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS subscription (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    status TEXT NOT NULL,
                    expires_at TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS subscription_v2 (
                    device_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    expires_at TEXT
                )
                """
            )
            connection.commit()

    def _device_state_key(self, device_id: str, key: str) -> str:
        device_id = (device_id or "").strip() or "default"
        return f"{device_id}:{key}"

    def _get_state(self, key: str) -> str | None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT value FROM app_state WHERE key = ?", (key,))
            row = cursor.fetchone()
        if row is None:
            return None
        return (row["value"] or "").strip() or None

    def _set_state(self, key: str, value: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO app_state (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
            connection.commit()

    def _plural_days_ru(self, n: int) -> str:
        n = abs(int(n))
        if 11 <= (n % 100) <= 14:
            return "дней"
        last = n % 10
        if last == 1:
            return "день"
        if 2 <= last <= 4:
            return "дня"
        return "дней"

    def get_subscription_status(self, device_id: str = "default") -> str:
        info = self.get_access_info(device_id=device_id)
        if info["subscription_active"]:
            expires_dt = info.get("subscription_expires_at")
            if isinstance(expires_dt, datetime):
                return f"Подписка: Активна до {expires_dt.strftime('%d.%m.%Y')}"
            return "Подписка: Активна"

        days_left = int(info.get("trial_days_left") or 0)
        if days_left > 0:
            return f"Бесплатно: осталось {days_left} {self._plural_days_ru(days_left)}"

        trial_end = info.get("trial_ends_at")
        if isinstance(trial_end, date):
            return f"Триал закончился {trial_end.strftime('%d.%m.%Y')} — нужна оплата"
        return "Триал закончился — нужна оплата"

    def get_access_info(self, device_id: str = "default") -> dict:
        result: dict = {
            "subscription_active": False,
            "subscription_expires_at": None,
            "trial_started_at": None,
            "trial_ends_at": None,
            "trial_days_passed": 0,
            "trial_days_left": 0,
            "trial_warning_day10": False,
            "trial_warning_day10_shown": False,
            "trial_warning_day10_should_show": False,
            "access_allowed": True,
        }

        row = None
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT status, expires_at FROM subscription_v2 WHERE device_id = ?",
                ((device_id or "").strip() or "default",),
            )
            row = cursor.fetchone()

        if row is not None:
            status = (row["status"] or "").strip().lower()
            expires_at = (row["expires_at"] or "").strip()
            if status == "active":
                if not expires_at:
                    result["subscription_active"] = True
                else:
                    try:
                        expires_dt = datetime.fromisoformat(expires_at)
                    except ValueError:
                        expires_dt = None
                    if expires_dt is None or expires_dt >= datetime.now():
                        result["subscription_active"] = True
                        result["subscription_expires_at"] = expires_dt

        started_raw = self._get_state(self._device_state_key(device_id, "trial_started_at"))
        if started_raw is None:
            started = date.today()
            self._set_state(self._device_state_key(device_id, "trial_started_at"), started.isoformat())
        else:
            try:
                started = datetime.fromisoformat(started_raw).date()
            except ValueError:
                try:
                    started = datetime.strptime(started_raw, "%Y-%m-%d").date()
                except Exception:
                    started = date.today()
                    self._set_state(self._device_state_key(device_id, "trial_started_at"), started.isoformat())

        today = date.today()
        days_passed = int((today - started).days)
        days_left = int(self.TRIAL_DAYS - days_passed)
        trial_end = started + timedelta(days=self.TRIAL_DAYS)

        result["trial_started_at"] = started
        result["trial_ends_at"] = trial_end
        result["trial_days_passed"] = days_passed
        result["trial_days_left"] = max(0, days_left)
        result["trial_warning_day10"] = days_passed >= 10 and days_left > 0
        warning_shown = self._get_state(self._device_state_key(device_id, self._TRIAL_WARNING_SHOWN_KEY)) == "1"
        result["trial_warning_day10_shown"] = warning_shown
        result["trial_warning_day10_should_show"] = bool(result["trial_warning_day10"] and not warning_shown)

        if result["subscription_active"]:
            result["access_allowed"] = True
        else:
            result["access_allowed"] = days_passed < self.TRIAL_DAYS

        return result

    def is_access_allowed(self, device_id: str = "default") -> bool:
        return bool(self.get_access_info(device_id=device_id).get("access_allowed"))

    def activate_subscription_days(self, device_id: str = "default", days: int | None = None) -> None:
        if days is None:
            days = self.SUBSCRIPTION_DAYS
        expires_at = (datetime.now() + timedelta(days=int(days))).isoformat(timespec="seconds")
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO subscription_v2 (device_id, status, expires_at)
                VALUES (?, 'active', ?)
                ON CONFLICT(device_id) DO UPDATE SET status = excluded.status, expires_at = excluded.expires_at
                """,
                ((device_id or "").strip() or "default", expires_at),
            )
            connection.commit()

    def activate_subscription_seconds(self, device_id: str = "default", seconds: int = 3600) -> None:
        seconds = int(seconds)
        if seconds <= 0:
            seconds = 3600
        expires_at = (datetime.now() + timedelta(seconds=seconds)).isoformat(timespec="seconds")
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO subscription_v2 (device_id, status, expires_at)
                VALUES (?, 'active', ?)
                ON CONFLICT(device_id) DO UPDATE SET status = excluded.status, expires_at = excluded.expires_at
                """,
                ((device_id or "").strip() or "default", expires_at),
            )
            connection.commit()

    def mark_trial_warning_day10_shown(self, device_id: str = "default") -> None:
        self._set_state(self._device_state_key(device_id, self._TRIAL_WARNING_SHOWN_KEY), "1")
