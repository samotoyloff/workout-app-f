import os
import smtplib
import socket
import logging
from email.message import EmailMessage


class EmailService:
    def __init__(self):
        self._log = logging.getLogger("workout_flow_pwa.email")
        self.host = (os.getenv("SMTP_HOST") or "").strip()
        self.user = (os.getenv("SMTP_USER") or "").strip()
        self.password = (os.getenv("SMTP_PASSWORD") or "").strip()
        self.from_email = (os.getenv("SMTP_FROM") or self.user).strip()

        try:
            self.port = int((os.getenv("SMTP_PORT") or "587").strip())
        except Exception:
            self.port = 587

        self.ssl = (os.getenv("SMTP_SSL") or "").strip() in ("1", "true", "yes", "on")
        self.starttls = (os.getenv("SMTP_STARTTLS") or "").strip() not in ("0", "false", "no", "off")
        try:
            self.timeout_seconds = int((os.getenv("SMTP_TIMEOUT_SECONDS") or "7").strip())
        except Exception:
            self.timeout_seconds = 7
        if self.timeout_seconds <= 0:
            self.timeout_seconds = 7

    def is_configured(self) -> bool:
        return bool(self.host and self.user and self.password and self.from_email)

    def send_login_code(self, to_email: str, code: str) -> None:
        if not self.is_configured():
            raise RuntimeError("SMTP не настроен")

        to_email = (to_email or "").strip().lower()
        if not to_email:
            raise ValueError("Email не задан")

        msg = EmailMessage()
        msg["Subject"] = "Workout Flow — код входа"
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg.set_content(
            "\n".join(
                [
                    "Код для входа в Workout Flow:",
                    "",
                    str(code),
                    "",
                    "Если вы не запрашивали код, просто игнорируйте это письмо.",
                ]
            )
        )

        try:
            if self.ssl:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout_seconds)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=self.timeout_seconds)

            try:
                server.ehlo()
                if not self.ssl and self.starttls:
                    server.starttls()
                    server.ehlo()
                server.login(self.user, self.password)
                server.send_message(msg)
            finally:
                try:
                    server.quit()
                except Exception:
                    pass
        except smtplib.SMTPAuthenticationError as e:
            self._log.exception("SMTP auth failed")
            raise RuntimeError("Почта не настроена: ошибка авторизации SMTP (логин/пароль).") from e
        except (socket.timeout, TimeoutError) as e:
            self._log.exception("SMTP timeout")
            raise RuntimeError(
                "Почта временно недоступна: сервер не может подключиться к SMTP (блокировка исходящей почты)."
            ) from e
        except Exception as e:
            self._log.exception("SMTP send failed")
            raise RuntimeError("Не удалось отправить код. Попробуйте позже.") from e
