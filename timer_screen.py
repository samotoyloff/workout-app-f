
import flet as ft
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
import time
import threading

class TimerScreen:
    def __init__(self, page, db):
        self.page = page
        self.db = db

        self._rest_running = False
        self._rest_paused = False
        self._rest_thread = None
        self._rest_initial_seconds = 0
        self._rest_seconds = 0
        self._rest_display = None
        self._tut_running = False
        self._tut_paused = False
        self._tut_thread = None
        self._tut_seconds = 0
        self._tut_display = None
        self._amrap_running = False
        self._amrap_paused = False
        self._amrap_thread = None
        self._amrap_seconds = 0
        self._amrap_display = None
        self._amrap_minutes_field = None

    async def _vibrate_async(self):
        try:
            import asyncio

            h = ft.HapticFeedback()
            for cycle in range(3):
                for _ in range(3):
                    try:
                        await h.heavy_impact()
                    except Exception:
                        pass
                    try:
                        await h.vibrate()
                    except Exception:
                        pass
                    try:
                        await asyncio.sleep(0.15)
                    except Exception:
                        pass
                    try:
                        await asyncio.sleep(0.3)
                    except Exception:
                        pass
        except Exception:
            pass

    def _show_timer_alert(self):
        try:
            alert = ft.AlertDialog(
                title=ft.Text("⏱ Таймер завершён!", size=20, weight=ft.FontWeight.BOLD, color="#EF4444"),
                content=ft.Text("Время вышло!", size=14, color="#D7ECFF"),
                actions=[
                    ft.TextButton("ОК", on_click=lambda _: self._close_alert()),
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
            )
            self.page.dialog = alert
            alert.open = True
            self.page.update()
        except Exception:
            pass

    def _close_alert(self):
        try:
            if self.page.dialog:
                self.page.dialog.open = False
                self.page.update()
        except Exception:
            pass

    def _notify_timer_done(self):
        try:
            if hasattr(self.page, "run_task"):
                self.page.run_task(self._vibrate_async)
        except Exception:
            pass

        try:
            self.page.run_thread(self._show_timer_alert)
        except Exception:
            pass

        try:
            import winsound
            for _ in range(3):
                winsound.MessageBeep()
                import time
                time.sleep(0.3)
        except Exception:
            pass
        
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

        def nav_tab(label: str, active: bool, on_click):
            return ft.Container(
                content=ft.Text(label, size=14, weight=ft.FontWeight.W_600, color="#D7ECFF" if active else "#9CCBFF"),
                alignment=ft.alignment.center,
                height=44,
                width=112,
                bgcolor="#2E86DE" if active else "#2B2F36",
                border_radius=ft.border_radius.all(22),
                on_click=on_click,
            )

        def go_calendar(_):
            from calendar_screen import CalendarScreen
            CalendarScreen(self.page, self.db).show()

        def go_training(_):
            from training_screen import TrainingScreen
            TrainingScreen(self.page, self.db).show()

        def go_timer(_):
            TimerScreen(self.page, self.db).show()

        def go_home(_):
            import main
            main.main(self.page)

        nav = ft.Row(
            [
                nav_tab("Даты", False, go_calendar),
                nav_tab("Трени", False, go_training),
                nav_tab("Таймеры", True, go_timer),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        )

        home_btn = ft.Container(
            content=ft.Text("⬅ На главную", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            height=44,
            alignment=ft.alignment.center,
            bgcolor="#2B2F36",
            border_radius=ft.border_radius.all(22),
            on_click=go_home,
        )

        title = ft.Text("ТАЙМЕР ОТДЫХА", size=18, weight=ft.FontWeight.W_600, color="#2E86DE")

        self._rest_display = ft.Text(
            self._format_mmss(self._rest_seconds),
            size=56,
            weight=ft.FontWeight.BOLD,
            color="#2E86DE",
        )

        def chip(label: str, seconds: int):
            return ft.Container(
                content=ft.Text(label, size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
                alignment=ft.alignment.center,
                height=44,
                width=102,
                bgcolor="#2B2F36",
                border_radius=ft.border_radius.all(22),
                on_click=lambda _: self._set_rest_seconds(seconds),
            )

        presets = ft.Row(
            [
                chip("60 сек", 60),
                chip("90 сек", 90),
                chip("120 сек", 120),
                ft.Container(width=4),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        )

        presets_box = ft.Container(
            width=328,
            alignment=ft.alignment.center,
            content=presets,
        )

        start_btn = ft.Container(
            content=ft.Text("СТАРТ", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            alignment=ft.alignment.center,
            height=52,
            width=318,
            bgcolor="#1F5FA9",
            border_radius=ft.border_radius.all(26),
            on_click=lambda _: self._start_rest(),
        )

        pause_btn = ft.Container(
            content=ft.Text("ПАУЗА", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            alignment=ft.alignment.center,
            height=44,
            width=156,
            bgcolor="#6B7280",
            border_radius=ft.border_radius.all(22),
            on_click=lambda _: self._toggle_pause_rest(),
        )

        reset_btn = ft.Container(
            content=ft.Text("СБРОС", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            alignment=ft.alignment.center,
            height=44,
            width=156,
            bgcolor="#374151",
            border_radius=ft.border_radius.all(22),
            on_click=lambda _: self._reset_rest(),
        )

        controls = ft.Container(
            width=328,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    ft.Row([start_btn, ft.Container(width=10)], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                    ft.Container(height=10),
                    ft.Row([pause_btn, reset_btn, ft.Container(width=4)], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        rest_card = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Container(height=6),
                    self._rest_display,
                    ft.Container(height=14),
                    presets_box,
                    ft.Container(height=14),
                    controls,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(16),
            bgcolor="#0F1720",
            border_radius=ft.border_radius.all(16),
            border=ft.border.all(1, "#1F2937") if hasattr(ft, "border") and hasattr(ft.border, "all") else None,
            width=360,
        )

        tut_amrap_title = ft.Text("ФУНКЦИОНАЛЬНЫЕ ТАЙМЕРЫ", size=16, weight=ft.FontWeight.W_600, color="#2E86DE")

        tut_block = ft.Container(
            content=ft.Column(
                [
                    ft.Text("TUT", size=26, weight=ft.FontWeight.BOLD, color="#22C55E"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(12),
            bgcolor="#0F1720",
            border_radius=ft.border_radius.all(16),
            expand=True,
            on_click=lambda _: self.show_tut(),
        )

        amrap_block = ft.Container(
            content=ft.Column(
                [
                    ft.Text("AMRAP", size=26, weight=ft.FontWeight.BOLD, color="#F59E0B"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(12),
            bgcolor="#0F1720",
            border_radius=ft.border_radius.all(16),
            expand=True,
            on_click=lambda _: self.show_amrap(),
        )

        bottom = ft.Container(
            content=ft.Column(
                [
                    tut_amrap_title,
                    ft.Container(height=10),
                    ft.Row([tut_block, ft.Container(width=12), amrap_block], spacing=0),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        self.page.add(
            mobile_frame(
                ft.Column(
                    [
                        ft.Container(height=10),
                        nav,
                        ft.Container(height=10),
                        home_btn,
                        ft.Container(height=16),
                        rest_card,
                        ft.Container(height=18),
                        bottom,
                        ft.Container(height=16),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                )
            )
        )
        self.page.update()

    def _format_mmss(self, seconds: int) -> str:
        mins, secs = divmod(max(0, int(seconds)), 60)
        return f"{mins:02d}:{secs:02d}"

    def show_tut(self):
        self._rest_running = False
        self._rest_paused = False
        self._amrap_running = False
        self._amrap_paused = False

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

        def nav_tab(label: str, active: bool, on_click):
            return ft.Container(
                content=ft.Text(label, size=14, weight=ft.FontWeight.W_600, color="#D7ECFF" if active else "#9CCBFF"),
                alignment=ft.alignment.center,
                height=44,
                width=112,
                bgcolor="#2E86DE" if active else "#2B2F36",
                border_radius=ft.border_radius.all(22),
                on_click=on_click,
            )

        def go_calendar(_):
            from calendar_screen import CalendarScreen
            CalendarScreen(self.page, self.db).show()

        def go_training(_):
            from training_screen import TrainingScreen
            TrainingScreen(self.page, self.db).show()

        def go_timer(_):
            TimerScreen(self.page, self.db).show()

        def go_home(_):
            import main
            main.main(self.page)

        nav = ft.Row(
            [
                nav_tab("Даты", False, go_calendar),
                nav_tab("Трени", False, go_training),
                nav_tab("Таймеры", True, go_timer),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        )

        home_btn = ft.Container(
            content=ft.Text("⬅ На главную", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            height=44,
            alignment=ft.alignment.center,
            bgcolor="#2B2F36",
            border_radius=ft.border_radius.all(22),
            on_click=go_home,
        )

        title = ft.Text("TUT", size=18, weight=ft.FontWeight.W_600, color="#22C55E")

        self._tut_display = ft.Text(
            self._format_mmss(self._tut_seconds),
            size=56,
            weight=ft.FontWeight.BOLD,
            color="#22C55E",
        )

        start_btn = ft.Container(
            content=ft.Text("СТАРТ", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            alignment=ft.alignment.center,
            height=52,
            width=318,
            bgcolor="#1F5FA9",
            border_radius=ft.border_radius.all(26),
            on_click=lambda _: self._start_tut(),
        )

        pause_btn = ft.Container(
            content=ft.Text("ПАУЗА", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            alignment=ft.alignment.center,
            height=52,
            width=318,
            bgcolor="#6B7280",
            border_radius=ft.border_radius.all(26),
            on_click=lambda _: self._toggle_pause_tut(),
        )

        reset_btn = ft.Container(
            content=ft.Text("СБРОС", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            alignment=ft.alignment.center,
            height=52,
            width=318,
            bgcolor="#374151",
            border_radius=ft.border_radius.all(26),
            on_click=lambda _: self._reset_tut(),
        )

        card = ft.Container(
            width=360,
            padding=ft.padding.all(16),
            bgcolor="#0F1720",
            border_radius=ft.border_radius.all(16),
            border=ft.border.all(1, "#1F2937") if hasattr(ft, "border") and hasattr(ft.border, "all") else None,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    title,
                    ft.Container(height=8),
                    self._tut_display,
                    ft.Container(height=18),
                    ft.Row([start_btn, ft.Container(width=10)], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                    ft.Container(height=10),
                    ft.Row([pause_btn, ft.Container(width=10)], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                    ft.Container(height=10),
                    ft.Row([reset_btn, ft.Container(width=10)], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
        )

        self.page.add(
            mobile_frame(
                ft.Column(
                    [
                        ft.Container(height=10),
                        nav,
                        ft.Container(height=10),
                        home_btn,
                        ft.Container(height=16),
                        card,
                        ft.Container(height=16),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                )
            )
        )
        self.page.update()

    def show_amrap(self):
        self._rest_running = False
        self._rest_paused = False
        self._tut_running = False
        self._tut_paused = False

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

        def nav_tab(label: str, active: bool, on_click):
            return ft.Container(
                content=ft.Text(label, size=14, weight=ft.FontWeight.W_600, color="#D7ECFF" if active else "#9CCBFF"),
                alignment=ft.alignment.center,
                height=44,
                width=112,
                bgcolor="#2E86DE" if active else "#2B2F36",
                border_radius=ft.border_radius.all(22),
                on_click=on_click,
            )

        def go_calendar(_):
            from calendar_screen import CalendarScreen
            CalendarScreen(self.page, self.db).show()

        def go_training(_):
            from training_screen import TrainingScreen
            TrainingScreen(self.page, self.db).show()

        def go_timer(_):
            TimerScreen(self.page, self.db).show()

        def go_home(_):
            import main
            main.main(self.page)

        nav = ft.Row(
            [
                nav_tab("Даты", False, go_calendar),
                nav_tab("Трени", False, go_training),
                nav_tab("Таймеры", True, go_timer),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        )

        home_btn = ft.Container(
            content=ft.Text("⬅ На главную", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            height=44,
            alignment=ft.alignment.center,
            bgcolor="#2B2F36",
            border_radius=ft.border_radius.all(22),
            on_click=go_home,
        )

        title = ft.Text("AMRAP", size=18, weight=ft.FontWeight.W_600, color="#F59E0B")

        self._amrap_display = ft.Text(
            self._format_mmss(self._amrap_seconds),
            size=56,
            weight=ft.FontWeight.BOLD,
            color="#F59E0B",
        )

        minutes_field = ft.TextField(
            label="Минуты",
            value="",
            width=200,
            border_color="#374151",
            bgcolor="#111827",
            color="#E5E7EB",
        )
        self._amrap_minutes_field = minutes_field

        def _apply_minutes_value(_=None):
            if self._amrap_running:
                return
            raw = (minutes_field.value or "").strip()
            try:
                minutes = int(raw) if raw else 0
            except Exception:
                minutes = 0
            if minutes < 0:
                minutes = 0
            self._amrap_seconds = minutes * 60
            if self._amrap_display is not None:
                self._amrap_display.value = self._format_mmss(self._amrap_seconds)
                self._amrap_display.color = "#F59E0B"
                try:
                    self.page.update()
                except Exception:
                    pass

        try:
            minutes_field.on_change = _apply_minutes_value
        except Exception:
            pass

        start_btn = ft.Container(
            content=ft.Text("СТАРТ", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            alignment=ft.alignment.center,
            height=52,
            width=318,
            bgcolor="#1F5FA9",
            border_radius=ft.border_radius.all(26),
            on_click=lambda _: self._start_amrap(),
        )

        pause_btn = ft.Container(
            content=ft.Text("ПАУЗА", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            alignment=ft.alignment.center,
            height=52,
            width=318,
            bgcolor="#6B7280",
            border_radius=ft.border_radius.all(26),
            on_click=lambda _: self._toggle_pause_amrap(),
        )

        reset_btn = ft.Container(
            content=ft.Text("СБРОС", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            alignment=ft.alignment.center,
            height=52,
            width=318,
            bgcolor="#374151",
            border_radius=ft.border_radius.all(26),
            on_click=lambda _: self._reset_amrap(),
        )

        card = ft.Container(
            width=360,
            padding=ft.padding.all(16),
            bgcolor="#0F1720",
            border_radius=ft.border_radius.all(16),
            border=ft.border.all(1, "#1F2937") if hasattr(ft, "border") and hasattr(ft.border, "all") else None,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    title,
                    ft.Container(height=8),
                    self._amrap_display,
                    ft.Container(height=14),
                    minutes_field,
                    ft.Container(height=18),
                    ft.Row([start_btn, ft.Container(width=10)], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                    ft.Container(height=10),
                    ft.Row([pause_btn, ft.Container(width=10)], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                    ft.Container(height=10),
                    ft.Row([reset_btn, ft.Container(width=10)], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
        )

        self.page.add(
            mobile_frame(
                ft.Column(
                    [
                        ft.Container(height=10),
                        nav,
                        ft.Container(height=10),
                        home_btn,
                        ft.Container(height=16),
                        card,
                        ft.Container(height=16),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                )
            )
        )
        self.page.update()

    def _set_rest_seconds(self, seconds: int) -> None:
        if self._rest_running:
            return
        self._rest_initial_seconds = int(seconds)
        self._rest_seconds = self._rest_initial_seconds
        if self._rest_display is not None:
            self._rest_display.value = self._format_mmss(self._rest_seconds)
            self._rest_display.color = "#2E86DE"
            self.page.update()

    def _start_rest(self) -> None:
        if self._rest_running and self._rest_paused:
            self._rest_paused = False
            return
        if self._rest_running:
            return
        if self._rest_seconds <= 0 and int(self._rest_initial_seconds or 0) > 0:
            self._rest_seconds = int(self._rest_initial_seconds)
            if self._rest_display is not None:
                self._rest_display.value = self._format_mmss(self._rest_seconds)
                self._rest_display.color = "#2E86DE"
                try:
                    self.page.update()
                except Exception:
                    pass
        if self._rest_seconds <= 0:
            return
        self._rest_running = True
        self._rest_paused = False
        self._rest_thread = threading.Thread(target=self._run_rest_timer, daemon=True)
        self._rest_thread.start()

    def _toggle_pause_rest(self) -> None:
        if not self._rest_running:
            return
        self._rest_paused = not self._rest_paused

    def _reset_rest(self) -> None:
        self._rest_running = False
        self._rest_paused = False
        self._rest_seconds = 0
        if self._rest_display is not None:
            self._rest_display.value = self._format_mmss(self._rest_seconds)
            self._rest_display.color = "#2E86DE"
            try:
                self.page.update()
            except Exception:
                pass

    def _run_rest_timer(self) -> None:
        try:
            while self._rest_running and self._rest_seconds > 0:
                if self._rest_paused:
                    time.sleep(0.2)
                    continue

                time.sleep(1)
                if not self._rest_running:
                    break
                if self._rest_paused:
                    continue

                self._rest_seconds -= 1
                if self._rest_display is not None:
                    val = self._format_mmss(self._rest_seconds)
                    def _update():
                        self._rest_display.value = val
                        self.page.update()
                    try:
                        self.page.run_thread(_update)
                    except Exception:
                        pass

            if not self._rest_running:
                return

            if self._rest_seconds <= 0 and self._rest_display is not None:
                def _update_done():
                    self._rest_display.value = "00:00"
                    self._rest_display.color = "#EF4444"
                    self.page.update()
                try:
                    self.page.run_thread(_update_done)
                except Exception:
                    pass
                self._notify_timer_done()
        finally:
            self._rest_running = False

    def _start_tut(self) -> None:
        if self._tut_running:
            if self._tut_paused:
                self._tut_paused = False
            return
        self._tut_running = True
        self._tut_paused = False
        self._tut_thread = threading.Thread(target=self._run_tut_timer, daemon=True)
        self._tut_thread.start()

    def _toggle_pause_tut(self) -> None:
        if not self._tut_running:
            return
        self._tut_paused = not self._tut_paused

    def _reset_tut(self) -> None:
        self._tut_running = False
        self._tut_paused = False
        self._tut_seconds = 0
        if self._tut_display is not None:
            self._tut_display.value = "00:00"
            try:
                self.page.update()
            except Exception:
                pass

    def _run_tut_timer(self) -> None:
        try:
            while self._tut_running:
                if self._tut_paused:
                    time.sleep(0.2)
                    continue
                time.sleep(1)
                if not self._tut_running or self._tut_paused:
                    continue
                self._tut_seconds += 1
                if self._tut_display is not None:
                    val = self._format_mmss(self._tut_seconds)
                    def _update():
                        self._tut_display.value = val
                        self.page.update()
                    try:
                        self.page.run_thread(_update)
                    except Exception:
                        pass
        finally:
            self._tut_running = False

    def _start_amrap(self) -> None:
        if self._amrap_running and self._amrap_paused:
            self._amrap_paused = False
            return
        if self._amrap_running:
            return

        if self._amrap_seconds <= 0 and self._amrap_minutes_field is not None:
            raw = (self._amrap_minutes_field.value or "").strip()
            try:
                minutes = int(raw) if raw else 0
            except Exception:
                minutes = 0
            if minutes < 0:
                minutes = 0
            self._amrap_seconds = minutes * 60
            if self._amrap_display is not None:
                self._amrap_display.value = self._format_mmss(self._amrap_seconds)
                self._amrap_display.color = "#F59E0B"
                try:
                    self.page.update()
                except Exception:
                    pass

        if self._amrap_seconds <= 0:
            return

        self._amrap_running = True
        self._amrap_paused = False
        self._amrap_thread = threading.Thread(target=self._run_amrap_timer, daemon=True)
        self._amrap_thread.start()

    def _toggle_pause_amrap(self) -> None:
        if not self._amrap_running:
            return
        self._amrap_paused = not self._amrap_paused

    def _reset_amrap(self) -> None:
        self._amrap_running = False
        self._amrap_paused = False
        self._amrap_seconds = 0
        if self._amrap_display is not None:
            self._amrap_display.value = "00:00"
            self._amrap_display.color = "#F59E0B"
            try:
                self.page.update()
            except Exception:
                pass

    def _run_amrap_timer(self) -> None:
        try:
            while self._amrap_running and self._amrap_seconds > 0:
                if self._amrap_paused:
                    time.sleep(0.2)
                    continue

                time.sleep(1)
                if not self._amrap_running:
                    break
                if self._amrap_paused:
                    continue

                self._amrap_seconds -= 1
                if self._amrap_display is not None:
                    val = self._format_mmss(self._amrap_seconds)
                    def _update():
                        self._amrap_display.value = val
                        self.page.update()
                    try:
                        self.page.run_thread(_update)
                    except Exception:
                        pass

            if not self._amrap_running:
                return

            if self._amrap_seconds <= 0 and self._amrap_display is not None:
                def _update_done():
                    self._amrap_display.value = "00:00"
                    self._amrap_display.color = "#EF4444"
                    self.page.update()
                try:
                    self.page.run_thread(_update_done)
                except Exception:
                    pass
                self._notify_timer_done()
        finally:
            self._amrap_running = False
    
    def _go_back(self):
        """Возврат на главный экран"""
        import main
        self.page.controls.clear()
        main.main(self.page)
