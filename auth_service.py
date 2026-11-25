import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from email_service import EmailService


class AuthService:
    CODE_TTL_MINUTES = 10
    SESSION_TTL_DAYS = 90

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
                CREATE TABLE IF NOT EXISTS auth_users (
                    email TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_codes (
                    email TEXT NOT NULL,
                    code_hash TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_codes_email ON auth_codes(email)")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    token_hash TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_email ON auth_sessions(email)")
            connection.commit()

    def _secret(self) -> str:
        return (os.getenv("AUTH_SECRET") or os.getenv("WORKOUT_API_TOKEN") or "change-me").strip()

    def _hash(self, value: str) -> str:
        raw = f"{self._secret()}:{value}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def start_login(self, email: str) -> None:
        email = (email or "").strip().lower()
        if not email or "@" not in email:
            raise ValueError("Введите корректный email")

        code = f"{secrets.randbelow(1000000):06d}"
        now = datetime.now()
        expires_at = (now + timedelta(minutes=self.CODE_TTL_MINUTES)).isoformat(timespec="seconds")
        code_hash = self._hash(f"code:{email}:{code}")

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO auth_users (email, created_at) VALUES (?, ?)",
                (email, now.isoformat(timespec="seconds")),
            )
            cursor.execute("DELETE FROM auth_codes WHERE email = ?", (email,))
            cursor.execute(
                """
                INSERT INTO auth_codes (email, code_hash, expires_at, attempts, created_at)
                VALUES (?, ?, ?, 0, ?)
                """,
                (email, code_hash, expires_at, now.isoformat(timespec="seconds")),
            )
            connection.commit()

        try:
            EmailService().send_login_code(email, code)
        except Exception as e:
            print(f"[ТЕСТОВЫЙ РЕЖИМ] Код для {email}: {code}")  # Покажем код в консоли локально
            if not os.getenv("SMTP_HOST"):
                print("[ТЕСТОВЫЙ РЕЖИМ] SMTP не настроен, используй код из консоли")

    def verify_code(self, email: str, code: str) -> str:
        email = (email or "").strip().lower()
        code = (code or "").strip()
        if not email or "@" not in email:
            raise ValueError("Введите корректный email")
        if not code or len(code) < 4:
            raise ValueError("Введите код")

        now = datetime.now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT email, code_hash, expires_at, attempts
                FROM auth_codes
                WHERE email = ?
                """,
                (email,),
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError("Код не найден. Запросите новый.")

            expires_at_raw = (row["expires_at"] or "").strip()
            try:
                expires_at = datetime.fromisoformat(expires_at_raw)
            except Exception:
                expires_at = now - timedelta(seconds=1)
            if expires_at < now:
                cursor.execute("DELETE FROM auth_codes WHERE email = ?", (email,))
                connection.commit()
                raise ValueError("Код просрочен. Запросите новый.")

            attempts = int(row["attempts"] or 0)
            if attempts >= 10:
                raise ValueError("Слишком много попыток. Запросите новый код.")

            expected = self._hash(f"code:{email}:{code}")
            if not secrets.compare_digest(expected, row["code_hash"]):
                cursor.execute("UPDATE auth_codes SET attempts = attempts + 1 WHERE email = ?", (email,))
                connection.commit()
                raise ValueError("Неверный код")

            cursor.execute("DELETE FROM auth_codes WHERE email = ?", (email,))
            token = secrets.token_urlsafe(32)
            token_hash = self._hash(f"token:{token}")
            expires_at_session = (now + timedelta(days=self.SESSION_TTL_DAYS)).isoformat(timespec="seconds")
            cursor.execute(
                """
                INSERT INTO auth_sessions (token_hash, email, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (token_hash, email, expires_at_session, now.isoformat(timespec="seconds")),
            )
            connection.commit()
            return token

    def get_email_by_token(self, token: str) -> str | None:
        token = (token or "").strip()
        if not token:
            return None
        now = datetime.now()
        token_hash = self._hash(f"token:{token}")
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT email, expires_at FROM auth_sessions WHERE token_hash = ?",
                (token_hash,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        expires_at_raw = (row["expires_at"] or "").strip()
        try:
            expires_at = datetime.fromisoformat(expires_at_raw)
        except Exception:
            return None
        if expires_at < now:
            return None
        return (row["email"] or "").strip().lower() or None

