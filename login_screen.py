import asyncio

import flet as ft

from auth_service import AuthService


class LoginScreen:
    def __init__(self, page: ft.Page, on_logged_in):
        self.page = page
        self.on_logged_in = on_logged_in
        self._auth = AuthService()

    def show(self):
        self.page.controls.clear()
        self.page.padding = 0
        try:
            self.page.bgcolor = "#0B0F14"
        except Exception:
            pass

        def mobile_frame(content):
            return ft.Container(
                expand=True,
                bgcolor="#0B0F14",
                alignment=ft.alignment.center,
                content=content,
            )

        title = ft.Text("Вход", size=22, weight=ft.FontWeight.W_600, color="#2E86DE")
        hint = ft.Text(
            "Введите email. Мы отправим код для входа.",
            size=14,
            color="#D7ECFF",
            text_align=ft.TextAlign.CENTER if hasattr(ft, "TextAlign") else None,
        )

        email_field = ft.TextField(
            label="Email",
            keyboard_type=ft.KeyboardType.EMAIL if hasattr(ft, "KeyboardType") else None,
            bgcolor="#111827",
            color="#E5E7EB",
            border_color="#374151",
            width=320,
        )

        code_field = ft.TextField(
            label="Код из письма",
            keyboard_type=ft.KeyboardType.NUMBER if hasattr(ft, "KeyboardType") else None,
            bgcolor="#111827",
            color="#E5E7EB",
            border_color="#374151",
            width=320,
            visible=False,
        )

        status_text = ft.Text("", size=13, color="#F6AD55")

        send_btn_text = ft.Text("ПОЛУЧИТЬ КОД", size=16, weight=ft.FontWeight.W_600, color="#D7ECFF")
        send_btn = ft.Container(
            content=send_btn_text,
            width=320,
            height=58,
            alignment=ft.alignment.center,
            bgcolor="#1F5FA9",
            border_radius=ft.border_radius.all(28),
        )

        verify_btn_text = ft.Text("ВОЙТИ", size=16, weight=ft.FontWeight.W_600, color="#D7ECFF")
        verify_btn = ft.Container(
            content=verify_btn_text,
            width=320,
            height=58,
            alignment=ft.alignment.center,
            bgcolor="#2563EB",
            border_radius=ft.border_radius.all(28),
            visible=False,
        )

        send_in_progress = False
        verify_in_progress = False

        def _send_code(_):
            email = (email_field.value or "").strip().lower()
            status_text.value = "Отправляем код..."
            status_text.color = "#F6AD55"
            send_btn.on_click = None
            self.page.update()
            try:
                self._auth.start_login(email)
            except Exception as e:
                status_text.value = str(e) or "Не удалось отправить код"
                status_text.color = "#EF4444"
                send_btn.on_click = _send_code
                self.page.update()
                return
            code_field.visible = True
            verify_btn.visible = True
            status_text.value = "Код отправлен. Проверьте почту (или консоль)."
            status_text.color = "#68D391"
            send_btn.on_click = _send_code
            self.page.update()

        def _verify(_):
            email = (email_field.value or "").strip().lower()
            code = (code_field.value or "").strip()
            status_text.value = "Проверяем код..."
            status_text.color = "#F6AD55"
            verify_btn.on_click = None
            self.page.update()
            try:
                token = self._auth.verify_code(email, code)
            except Exception as e:
                status_text.value = str(e) or "Не удалось войти"
                status_text.color = "#EF4444"
                verify_btn.on_click = _verify
                self.page.update()
                return

            try:
                setattr(self.page, "_wf_user_id", email)
            except Exception:
                pass

            verify_btn.on_click = _verify
            if callable(self.on_logged_in):
                self.on_logged_in()

        send_btn.on_click = _send_code
        verify_btn.on_click = _verify

        layout = ft.Column(
            [
                ft.Container(height=30),
                ft.Container(alignment=ft.alignment.center, content=title),
                ft.Container(height=10),
                ft.Container(width=320, alignment=ft.alignment.center, content=hint),
                ft.Container(height=16),
                ft.Container(alignment=ft.alignment.center, content=email_field),
                ft.Container(height=12),
                ft.Container(alignment=ft.alignment.center, content=code_field),
                ft.Container(height=10),
                ft.Container(alignment=ft.alignment.center, content=status_text),
                ft.Container(height=16),
                ft.Container(alignment=ft.alignment.center, content=send_btn),
                ft.Container(height=12),
                ft.Container(alignment=ft.alignment.center, content=verify_btn),
                ft.Container(height=30),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.page.add(mobile_frame(layout))
        self.page.update()
