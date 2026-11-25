
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
from datetime import datetime
from sync_service import SyncService

class TrainingScreen:
    def __init__(self, page, db, selected_date=None):
        self.page = page
        self.db = db
        self.selected_date = selected_date
        
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

        initial_date = self.selected_date
        if initial_date is None:
            initial_date = datetime.now().date()
        elif isinstance(initial_date, str):
            try:
                initial_date = datetime.strptime(initial_date, "%Y-%m-%d").date()
            except Exception:
                initial_date = datetime.now().date()
        elif isinstance(initial_date, datetime):
            initial_date = initial_date.date()

        title = ft.Text(
            f"FLOW: {initial_date.strftime('%d.%m.%Y')}",
            size=20,
            weight=ft.FontWeight.BOLD,
            color="#2E86DE",
        )

        def _current_selected_date():
            return initial_date

        def go_calendar(_):
            from calendar_screen import CalendarScreen
            CalendarScreen(self.page, self.db, month_anchor=_current_selected_date()).show()

        def go_training(_):
            TrainingScreen(self.page, self.db, selected_date=_current_selected_date()).show()

        def go_timer(_):
            from timer_screen import TimerScreen
            TimerScreen(self.page, self.db).show()

        def go_home(_):
            import main
            main.main(self.page)

        nav = ft.Row(
            [
                nav_tab("Даты", False, go_calendar),
                nav_tab("Трени", True, go_training),
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

        content_field = ft.TextField(
            label="Тренировка",
            multiline=True,
            height=300,
            border_color="#374151",
            bgcolor="#111827",
            color="#E5E7EB",
        )

        notes_field = ft.TextField(
            label="Заметки",
            multiline=True,
            height=80,
            border_color="#374151",
            bgcolor="#111827",
            color="#E5E7EB",
        )

        save_btn_text = ft.Text("СОХРАНИТЬ", size=14, weight=ft.FontWeight.W_600, color="#0B0F14")

        save_btn = ft.Container(
            content=save_btn_text,
            height=56,
            width=360,
            alignment=ft.alignment.center,
            bgcolor="#22C55E",
            border_radius=ft.border_radius.all(28),
        )

        def _set_save_state(state: str):
            if state == "saved":
                save_btn.bgcolor = "#2563EB"
                save_btn_text.value = "СОХРАНЕНО"
                save_btn_text.color = "#D7ECFF"
            elif state == "deleted":
                save_btn.bgcolor = "#EF4444"
                save_btn_text.value = "УДАЛЕНО"
                save_btn_text.color = "#0B0F14"
            else:
                save_btn.bgcolor = "#22C55E"
                save_btn_text.value = "СОХРАНИТЬ"
                save_btn_text.color = "#0B0F14"
            try:
                self.page.update()
            except Exception:
                pass

        def _mark_dirty(_=None):
            _set_save_state("default")

        existing = None
        try:
            user_id = getattr(self.page, "_wf_user_id", None) or "default"
            existing = self.db.get_latest_workout_by_date(initial_date, user_id=user_id)
        except Exception:
            existing = None

        if existing:
            try:
                content_field.value = existing.get("content", "") or ""
                notes_field.value = existing.get("notes", "") or ""
            except Exception:
                pass
        else:
            _set_save_state("default")

        try:
            content_field.on_change = _mark_dirty
            notes_field.on_change = _mark_dirty
        except Exception:
            pass

        sync_service = SyncService(self.page, self.db)

        def save_workout(e):
            content_value = (content_field.value or "").strip()
            notes_value = (notes_field.value or "").strip()
            workout_date = initial_date
            workout_date_key = workout_date.strftime("%Y-%m-%d")
            user_id = getattr(self.page, "_wf_user_id", None) or "default"

            try:
                if not content_value and not notes_value:
                    self.db.delete_workouts_by_date(workout_date, user_id=user_id)
                    sync_service.clear_pending(workout_date_key)
                    sync_service.remove_snapshot(workout_date_key)
                    # Попробуем синхронизировать удаление с сервером
                    try:
                        sync_service.flush_pending()
                    except Exception:
                        pass
                    self._show_success("Запись удалена!")
                    _set_save_state("deleted")
                    return

                self.db.replace_workout_by_date(date=workout_date, content=content_value, notes=notes_value, user_id=user_id)
                sync_service.clear_pending(workout_date_key)
                sync_service.store_snapshot(workout_date_key, content_value, notes_value)
                # Попробуем синхронизировать сохранение с сервером
                try:
                    sync_service.flush_pending()
                except Exception:
                    pass
                self._show_success("Сохранено!")
                _set_save_state("saved")
            except Exception:
                if not content_value and not notes_value:
                    sync_service.queue_delete(workout_date_key)
                else:
                    sync_service.queue_upsert(workout_date_key, content_value, notes_value)
                self._show_success("Сохранено локально. Синхронизация при подключении.")
                _set_save_state("saved")

        save_btn.on_click = save_workout

        card = ft.Container(
            content=ft.Column(
                [
                    content_field,
                    ft.Container(height=12),
                    notes_field,
                ],
                spacing=0,
            ),
            padding=ft.padding.all(14),
            bgcolor="#0F1720",
            border_radius=ft.border_radius.all(16),
            border=ft.border.all(1, "#1F2937") if hasattr(ft, "border") and hasattr(ft.border, "all") else None,
            width=360,
        )

        content_area = ft.Column(
            [
                ft.Container(height=10),
                nav,
                ft.Container(height=10),
                home_btn,
                ft.Container(height=16),
                title,
                ft.Container(height=14),
                card,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )

        layout = ft.Column(
            [
                ft.Container(expand=True, content=content_area),
                save_btn,
                ft.Container(height=10),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )
        try:
            layout.expand = True
        except Exception:
            pass

        self.page.add(mobile_frame(layout))
        self.page.update()
    
    def _show_error(self, message):
        """Показывает сообщение об ошибке"""
        dialog = ft.AlertDialog(
            title=ft.Text("Ошибка"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("ОК", on_click=lambda _: self._close_dialog())
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_success(self, message):
        """Показывает сообщение об успехе"""
        dialog = ft.AlertDialog(
            title=ft.Text("Успех"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("ОК", on_click=lambda _: self._close_dialog())
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _close_dialog(self):
        """Закрывает диалог"""
        self.page.dialog.open = False
        self.page.update()
    
    def _clear_fields(self, date_field, content_field, notes_field):
        """Очищает поля формы"""
        content_field.value = ""
        notes_field.value = ""
        self.page.update()
    
    def _go_back(self):
        """Возврат на главный экран"""
        import main
        self.page.controls.clear()
        main.main(self.page)
