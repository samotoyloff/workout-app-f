
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
import sqlite3
import datetime
from datetime import datetime, date

class CalendarScreen:
    def __init__(self, page, db, month_anchor=None):
        self.page = page
        self.db = db
        anchor = month_anchor
        if anchor is None:
            anchor = datetime.now().date()
        elif isinstance(anchor, str):
            try:
                anchor = datetime.strptime(anchor, "%Y-%m-%d").date()
            except Exception:
                anchor = datetime.now().date()
        elif isinstance(anchor, datetime):
            anchor = anchor.date()
        self._month_anchor = anchor.replace(day=1)
        
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
            CalendarScreen(self.page, self.db).show()

        def go_training(_):
            from training_screen import TrainingScreen
            TrainingScreen(self.page, self.db).show()

        def go_timer(_):
            from timer_screen import TimerScreen
            TimerScreen(self.page, self.db).show()

        def go_home(_):
            import main
            main.main(self.page)

        nav = ft.Row(
            [
                nav_tab("Даты", True, go_calendar),
                nav_tab("Трени", False, go_training),
                nav_tab("Таймеры", False, go_timer),
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

        months_ru = [
            "Янв",
            "Фев",
            "Мар",
            "Апр",
            "Май",
            "Июн",
            "Июл",
            "Авг",
            "Сен",
            "Окт",
            "Ноя",
            "Дек",
        ]
        month_title = f"{months_ru[self._month_anchor.month - 1]} {self._month_anchor.year}"

        header = ft.Text(
            month_title,
            size=22,
            weight=ft.FontWeight.W_600,
            color="#2E86DE",
        )

        calendar_dates = self._generate_calendar_dates(self._month_anchor)

        weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        weekday_row = ft.Row(
            [
                ft.Container(
                    content=ft.Text(day, size=12, weight=ft.FontWeight.W_600, color="#A0AEC0"),
                    width=44,
                    height=32,
                    alignment=ft.alignment.center,
                )
                for day in weekdays
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        calendar_grid = ft.Column([weekday_row], spacing=8)
        week_row = ft.Row([], alignment=ft.MainAxisAlignment.CENTER, spacing=8)

        for day_info in calendar_dates:
            day_value = day_info["day"]
            day_date = day_info["date"]
            has_workouts = day_info["has_workouts"]
            is_today = day_info["is_today"]

            if not day_date:
                day_cell = ft.Container(width=44, height=44)
            else:
                if is_today:
                    bgcolor = "#2E86DE"
                    text_color = "#0B0F14"
                elif has_workouts:
                    bgcolor = "#1F5FA9"
                    text_color = "#D7ECFF"
                else:
                    bgcolor = "#2B2F36"
                    text_color = "#D1D5DB"

                day_cell = ft.Container(
                    content=ft.Text(str(day_value), size=14, weight=ft.FontWeight.W_600, color=text_color),
                    width=44,
                    height=44,
                    alignment=ft.alignment.center,
                    bgcolor=bgcolor,
                    border_radius=ft.border_radius.all(12),
                    on_click=lambda e, d=day_date: self._on_date_click(d),
                )

            week_row.controls.append(day_cell)

            if len(week_row.controls) == 7:
                calendar_grid.controls.append(week_row)
                week_row = ft.Row([], alignment=ft.MainAxisAlignment.CENTER, spacing=8)

        if week_row.controls:
            calendar_grid.controls.append(week_row)

        def set_month(month_index: int):
            self._month_anchor = date(self._month_anchor.year, month_index, 1)
            self.show()

        months_buttons = ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(months_ru[i], size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
                            alignment=ft.alignment.center,
                            height=44,
                            expand=True,
                            bgcolor="#2B2F36",
                            border_radius=ft.border_radius.all(22),
                            on_click=lambda e, m=i+1: set_month(m),
                        )
                        for i in range(row*3, row*3+3)
                    ],
                    spacing=12,
                )
                for row in range(4)
            ],
            spacing=12,
        )

        today_btn = ft.Container(
            content=ft.Text("СЕГОДНЯ", size=14, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            height=52,
            alignment=ft.alignment.center,
            bgcolor="#1F5FA9",
            border_radius=ft.border_radius.all(26),
            on_click=lambda _: self._go_today(),
        )

        self.page.add(
            mobile_frame(
                ft.Column(
                    [
                        ft.Container(height=10),
                        nav,
                        ft.Container(height=10),
                        home_btn,
                        ft.Container(height=18),
                        header,
                        ft.Container(height=10),
                        calendar_grid,
                        ft.Container(height=18),
                        today_btn,
                        ft.Container(height=18),
                        ft.Text("Выбор месяца", size=16, weight=ft.FontWeight.W_600, color="#E5E7EB"),
                        ft.Container(height=10),
                        months_buttons,
                        ft.Container(height=24),
                        ft.Container(height=16),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                )
            )
        )
        self.page.update()
    
    def _generate_calendar_dates(self, month_anchor):
        year = month_anchor.year
        month = month_anchor.month
        
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()  # 0=Пн, 6=Вс
        
        if month == 12:
            next_month = date(year+1, 1, 1)
        else:
            next_month = date(year, month+1, 1)
        days_in_month = (next_month - first_day).days
        
        dates = []
        
        for _ in range(first_weekday):
            dates.append({
                'day': '',
                'date': None,
                'has_workouts': False,
                'is_today': False
            })
        
        for day in range(1, days_in_month+1):
            current_day_date = date(year, month, day)
            today = datetime.now().date()
            user_id = getattr(self.page, "_wf_user_id", None) or "default"
            workouts = self.db.get_workouts_by_date(current_day_date, user_id=user_id)
            dates.append({
                'day': day,
                'date': current_day_date,
                'has_workouts': bool(workouts),
                'is_today': current_day_date == today
            })

        while len(dates) % 7 != 0:
            dates.append({
                'day': '',
                'date': None,
                'has_workouts': False,
                'is_today': False
            })

        while len(dates) < 42:
            dates.append({
                'day': '',
                'date': None,
                'has_workouts': False,
                'is_today': False
            })

        return dates
    
    def _on_date_click(self, selected_date):
        """Обработка клика по дате"""
        if not selected_date:
            return

        from training_screen import TrainingScreen
        TrainingScreen(self.page, self.db, selected_date=selected_date).show()
    
    def _show_workouts_dialog(self, selected_date, workouts):
        """Показывает диалог с тренировками"""
        dialog = ft.AlertDialog(
            title=ft.Text(f"Тренировки за {selected_date.strftime('%d.%m.%Y')}"),
            content=ft.Column([
                ft.Text(f"Тренировка: {workout['content']}", size=14)
                for workout in workouts
            ], height=200, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Закрыть", on_click=lambda _: self._close_dialog())
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_no_workouts_dialog(self, selected_date):
        """Показывает диалог что тренировок нет"""
        dialog = ft.AlertDialog(
            title=ft.Text(f"{selected_date.strftime('%d.%m.%Y')}"),
            content=ft.Text("В этот день нет тренировок"),
            actions=[
                ft.TextButton("Закрыть", on_click=lambda _: self._close_dialog())
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _close_dialog(self):
        """Закрывает диалог"""
        self.page.dialog.open = False
        self.page.update()

    def _go_today(self):
        today = datetime.now().date()
        from training_screen import TrainingScreen
        TrainingScreen(self.page, self.db, selected_date=today).show()
    
    def _go_back(self):
        """Возврат на главный экран"""
        import main
        self.page.controls.clear()
        main.main(self.page)
