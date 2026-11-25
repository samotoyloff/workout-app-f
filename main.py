
try:
    import flet as ft
except ModuleNotFoundError as e:
    raise SystemExit("Не установлен пакет flet. Установи: py -m pip install flet") from e

import asyncio

if not hasattr(ft, "colors") and hasattr(ft, "Colors"):
    ft.colors = ft.Colors
if not hasattr(ft, "icons") and hasattr(ft, "Icons"):
    ft.icons = ft.Icons
if hasattr(ft, "alignment") and not hasattr(ft.alignment, "center"):
    if hasattr(ft, "Alignment"):
        try:
            ft.alignment.center = ft.Alignment(0, 0)
        except TypeError:
            ft.alignment.center = ft.Alignment()
    else:
        ft.alignment.center = 0
if hasattr(ft, "padding") and not hasattr(ft.padding, "all"):
    def _padding_all(value):
        if hasattr(ft, "Padding"):
            try:
                return ft.Padding(value)
            except TypeError:
                try:
                    return ft.Padding(left=value, top=value, right=value, bottom=value)
                except TypeError:
                    return ft.Padding(value, value, value, value)
        if hasattr(ft.padding, "symmetric"):
            try:
                return ft.padding.symmetric(horizontal=value, vertical=value)
            except TypeError:
                try:
                    return ft.padding.symmetric(value, value)
                except TypeError:
                    return ft.padding.symmetric(value)
        return value

    ft.padding.all = _padding_all
if hasattr(ft, "border_radius") and not hasattr(ft.border_radius, "all"):
    def _border_radius_all(value):
        if hasattr(ft, "BorderRadius"):
            try:
                return ft.BorderRadius(value)
            except TypeError:
                try:
                    return ft.BorderRadius(top_left=value, top_right=value, bottom_left=value, bottom_right=value)
                except TypeError:
                    return ft.BorderRadius(value, value, value, value)
        return value

    ft.border_radius.all = _border_radius_all
import sqlite3
import datetime
from calendar_screen import CalendarScreen
from training_screen import TrainingScreen
from timer_screen import TimerScreen
from database_helper import DatabaseHelper
from sync_service import SyncService
from device_service import DeviceService
from login_screen import LoginScreen
from auth_service import AuthService

def main(page: ft.Page):
    page.title = "Workout Flow"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    try:
        page.bgcolor = "#0B0F14"
    except Exception:
        pass

    db = DatabaseHelper()
    sync_service = SyncService(page, db)
    device_service = DeviceService(page)
    auth_service = AuthService()
    footer_url = "https://serjsamotoyloff.ru/p/1101514/"
    pc_app_url = "https://serjsamotoyloff.ru/p/1101514/"

    def _open_footer_url(_):
        if hasattr(page, "launch_url"):
            try:
                page.launch_url(footer_url)
                return
            except Exception:
                pass
        __import__("webbrowser").open(footer_url)

    def _mobile_frame(content):
        return ft.Container(
            expand=True,
            bgcolor="#0B0F14",
            alignment=ft.alignment.center,
            content=content,
        )

    def _pill_button(label_text: str, on_click, bgcolor: str = "#1F5FA9"):
        return ft.Container(
            content=ft.Text(label_text, size=16, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            width=320,
            height=58,
            alignment=ft.alignment.center,
            bgcolor=bgcolor,
            border_radius=ft.border_radius.all(28),
            on_click=on_click,
        )

    def show_login_screen():
        LoginScreen(page, on_logged_in=show_main_screen).show()

    async def _logout_async():
        try:
            prefs = ft.SharedPreferences()
            await prefs.remove("wf_user_token")
        except Exception:
            pass
        try:
            setattr(page, "_wf_user_id", None)
        except Exception:
            pass
        try:
            if hasattr(page, "run_thread"):
                page.run_thread(show_login_screen)
            else:
                show_login_screen()
        except Exception:
            pass

    def show_main_screen():
        page.controls.clear()
        page.dialog = None
        # Синхронизация с сервером (закомментирована для APK)
        # try:
        #     sync_service.flush_pending()
        # except Exception:
        #     pass

        user_id = getattr(page, "_wf_user_id", None)
        if not user_id:
            user_id = "local_user"
            try:
                setattr(page, "_wf_user_id", user_id)
            except Exception:
                pass

        try:
            title = ft.Text(
                "Дневник Тренировок Workout Flow",
                size=22,
                weight=ft.FontWeight.W_600,
                color="#2E86DE",
                text_align=ft.TextAlign.CENTER,
            )
        except Exception:
            title = ft.Text(
                "Дневник Тренировок Workout Flow",
                size=22,
                weight=ft.FontWeight.W_600,
                color="#2E86DE",
            )

        user_text = ft.Text(
            "Локальный режим (без синхронизации)",
            size=12,
            color="#9CCBFF",
        )

        def _logout(_):
            pass

        logout_btn = ft.Container(width=0, height=0)

        def _open_settings(_):
            dlg = ft.AlertDialog(
                title=ft.Text("Синхронизация"),
                content=ft.Text("В этой версии синхронизация с сервером отключена. Данные хранятся только на вашем устройстве."),
                actions=[
                    ft.TextButton("ОК", on_click=lambda _: close_dialog()),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.dialog = dlg
            dlg.open = True
            page.update()

        settings_btn = ft.Container(width=0, height=0)

        def save_settings(new_url, new_token):
            async def save():
                try:
                    sync_service = SyncService(page, db)
                    await sync_service.set_api_credentials(new_url.strip(), new_token.strip())
                    close_dialog()
                    show_main_screen()
                except Exception:
                    pass
            page.run_task(save)

        def _open_calendar(_):
            show_calendar_screen()

        def _open_training(_):
            show_training_screen()

        def _open_timer(_):
            show_timer_screen()

        pc_app_url = "https://serjsamotoyloff.ru/d/sof-4"
        online_support_url = "https://serjsamotoyloff.ru/"

        def _open_pc_app_link(_):
            __import__("webbrowser").open(pc_app_url)

        def _open_online_support(_):
            __import__("webbrowser").open(online_support_url)

        pc_app_link = ft.TextButton(
            content=ft.Row([
                ft.Text("🖥️ Приложение для ПК", size=14, color="#D7ECFF"),
                ft.Text("→", size=14, color="#2E86DE"),
            ], alignment=ft.MainAxisAlignment.CENTER),
            on_click=_open_pc_app_link,
        )

        online_support_link = ft.TextButton(
            content=ft.Text("Сопровождение онлайн — ДИС", size=14, color="#2E86DE"),
            on_click=_open_online_support,
        )

        buttons = ft.Column([
            _pill_button("ДАТЫ", _open_calendar),
            ft.Container(height=14),
            _pill_button("ТРЕНИ", _open_training, bgcolor="#3D8FD6"),
            ft.Container(height=14),
            _pill_button("ТАЙМЕРЫ", _open_timer),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        try:
            footer_text = ft.Text("samotoyloff soft", size=12, color="#2E86DE", weight=ft.FontWeight.W_600)
        except Exception:
            footer_text = ft.Text("samotoyloff soft", size=12, color="#2E86DE")

        try:
            footer_text.style = ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE)
        except Exception:
            pass

        try:
            footer_link = ft.TextButton(content=footer_text, url=footer_url, url_target="_self")
        except Exception:
            try:
                footer_link = ft.TextButton("samotoyloff soft", url=footer_url)
            except Exception:
                footer_link = ft.TextButton(content=footer_text, on_click=_open_footer_url)

        links_column = ft.Column([
            pc_app_link,
            online_support_link,
            footer_link,
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, tight=True)

        page.add(_mobile_frame(
            ft.Column([
                ft.Container(height=20),
                ft.Container(alignment=ft.alignment.center, content=title),
                ft.Container(height=8),
                ft.Container(alignment=ft.alignment.center, content=user_text),
                ft.Container(height=6),
                ft.Row([
                    ft.Container(alignment=ft.alignment.center, content=logout_btn),
                    ft.Container(alignment=ft.alignment.center, content=settings_btn),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ft.Container(height=20),
                ft.Container(alignment=ft.alignment.center, content=buttons),
                ft.Container(expand=1),
                links_column,
                ft.Container(height=20),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START, scroll=ft.ScrollMode.AUTO)
        ))
        page.update()

    def show_calendar_screen():
        calendar_screen = CalendarScreen(page, db)
        calendar_screen.show()

    def show_training_screen():
        training_screen = TrainingScreen(page, db)
        training_screen.show()

    def show_timer_screen():
        timer_screen = TimerScreen(page, db)
        timer_screen.show()

    # Для локального режима (APK) — сразу открываем главный экран без авторизации
    show_main_screen()

if __name__ == "__main__":
    # Для сборки APK flet-cli сам подставит правильный view
    # Для локального запуска — десктопное окно
    ft.app(target=main)
