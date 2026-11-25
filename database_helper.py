import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any


class DatabaseHelper:
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
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workout_date TEXT NOT NULL,
                    user_id TEXT NOT NULL DEFAULT 'default',
                    content TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workouts_date ON workouts(workout_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workouts_user_date ON workouts(user_id, workout_date)")

            cursor.execute("PRAGMA table_info(workouts)")
            cols = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in cols:
                cursor.execute("ALTER TABLE workouts ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_workouts_user_date ON workouts(user_id, workout_date)")
            connection.commit()

    def _normalize_date(self, value: Any) -> str:
        if isinstance(value, str):
            parsed = datetime.strptime(value, "%Y-%m-%d").date()
            return parsed.strftime("%Y-%m-%d")
        if isinstance(value, datetime):
            return value.date().strftime("%Y-%m-%d")
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        raise TypeError("date должен быть datetime.date, datetime.datetime или строкой YYYY-MM-DD")

    def add_workout(self, date: date | datetime | str, content: str, notes: str = "", user_id: str = "default") -> int:
        workout_date = self._normalize_date(date)
        user_id = (user_id or "").strip() or "default"
        content = (content or "").strip()
        notes = (notes or "").strip()
        if not content and not notes:
            raise ValueError("Нужно заполнить тренировку или заметки")

        created_at = datetime.now().isoformat(timespec="seconds")

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO workouts (workout_date, user_id, content, notes, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (workout_date, user_id, content, notes, created_at),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def delete_workouts_by_date(self, date: date | datetime | str, user_id: str = "default") -> int:
        workout_date = self._normalize_date(date)
        user_id = (user_id or "").strip() or "default"

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM workouts WHERE user_id = ? AND workout_date = ?", (user_id, workout_date))
            deleted = int(cursor.rowcount or 0)
            connection.commit()
            return deleted

    def replace_workout_by_date(self, date: date | datetime | str, content: str, notes: str = "", user_id: str = "default") -> int:
        workout_date = self._normalize_date(date)
        user_id = (user_id or "").strip() or "default"
        content = (content or "").strip()
        notes = (notes or "").strip()
        if not content and not notes:
            raise ValueError("Нужно заполнить тренировку или заметки")

        created_at = datetime.now().isoformat(timespec="seconds")

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM workouts WHERE user_id = ? AND workout_date = ?", (user_id, workout_date))
            cursor.execute(
                """
                INSERT INTO workouts (workout_date, user_id, content, notes, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (workout_date, user_id, content, notes, created_at),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update_workout(self, workout_id: int, content: str, notes: str = "") -> None:
        content = (content or "").strip()
        notes = (notes or "").strip()
        if not content and not notes:
            raise ValueError("Нужно заполнить тренировку или заметки")

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE workouts
                SET content = ?, notes = ?
                WHERE id = ?
                """,
                (content, notes, int(workout_id)),
            )
            connection.commit()

    def get_latest_workout_by_date(self, date: date | datetime | str, user_id: str = "default") -> dict[str, Any] | None:
        workouts = self.get_workouts_by_date(date, user_id=user_id)
        if not workouts:
            return None
        return workouts[0]

    def upsert_workout_by_date(self, date: date | datetime | str, content: str, notes: str = "", user_id: str = "default") -> int:
        existing = self.get_latest_workout_by_date(date, user_id=user_id)
        if existing is None:
            return self.add_workout(date=date, content=content, notes=notes, user_id=user_id)
        self.update_workout(existing["id"], content=content, notes=notes)
        return int(existing["id"])

    def get_workouts_by_date(self, date: date | datetime | str, user_id: str = "default") -> list[dict[str, Any]]:
        workout_date = self._normalize_date(date)
        user_id = (user_id or "").strip() or "default"

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT id, workout_date, user_id, content, notes, created_at
                FROM workouts
                WHERE user_id = ? AND workout_date = ?
                ORDER BY id DESC
                """,
                (user_id, workout_date),
            )
            rows = cursor.fetchall()

        return [
            {
                "id": int(row["id"]),
                "date": row["workout_date"],
                "user_id": row["user_id"],
                "content": row["content"],
                "notes": row["notes"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def list_workouts(
        self,
        date_from: str | date | datetime | None = None,
        date_to: str | date | datetime | None = None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        if user_id is not None:
            clauses.append("user_id = ?")
            params.append((user_id or "").strip() or "default")
        if date_from is not None:
            clauses.append("workout_date >= ?")
            params.append(self._normalize_date(date_from))
        if date_to is not None:
            clauses.append("workout_date <= ?")
            params.append(self._normalize_date(date_to))

        where_sql = ""
        if clauses:
            where_sql = "WHERE " + " AND ".join(clauses)

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"""
                SELECT id, workout_date, user_id, content, notes, created_at
                FROM workouts
                {where_sql}
                ORDER BY workout_date DESC, id DESC
                """,
                tuple(params),
            )
            rows = cursor.fetchall()

        return [
            {
                "id": int(row["id"]),
                "date": row["workout_date"],
                "user_id": row["user_id"],
                "content": row["content"],
                "notes": row["notes"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
