import flet as ft
import asyncio
import inspect
import os
from decimal import Decimal

from yookassa_service import YooKassaService


class PaywallScreen:
    def __init__(self, page: ft.Page, subscription_service, on_back=None):
        self.page = page
        self.subscription_service = subscription_service
        self.on_back = on_back

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

        user_id = getattr(self.page, "_wf_user_id", None) or "default"
        info = self.subscription_service.get_access_info(device_id=user_id)
        trial_end = info.get("trial_ends_at")
        trial_end_text = ""
        try:
            trial_end_text = trial_end.strftime("%d.%m.%Y")
        except Exception:
            trial_end_text = ""

        title = ft.Text(
            "Нужна подписка",
            size=22,
            weight=ft.FontWeight.W_600,
            color="#2E86DE",
            text_align=ft.TextAlign.CENTER if hasattr(ft, "TextAlign") else None,
        )

        payment_mode = (os.getenv("PAYMENT_MODE") or "prod").strip().lower()
        if payment_mode == "test":
            price_text = (os.getenv("PAYMENT_TEST_PRICE_RUB") or "1.00").strip()
            duration_seconds_text = (os.getenv("PAYMENT_TEST_DURATION_SECONDS") or "3600").strip()
            try:
                duration_seconds = int(duration_seconds_text)
            except Exception:
                duration_seconds = 3600
            if duration_seconds <= 0:
                duration_seconds = 3600
            duration_title = "1 час"
            if duration_seconds != 3600:
                duration_title = f"{duration_seconds} сек"
        else:
            price_text = (os.getenv("PAYMENT_PRICE_RUB") or "299.00").strip()
            duration_days_text = (os.getenv("PAYMENT_DURATION_DAYS") or "30").strip()
            try:
                duration_days = int(duration_days_text)
            except Exception:
                duration_days = 30
            if duration_days <= 0:
                duration_days = 30
            duration_title = f"{duration_days} дней"

        try:
            price_amount = Decimal(price_text)
        except Exception:
            price_amount = Decimal("299.00") if payment_mode != "test" else Decimal("1.00")

        lines = [
            "Ваш бесплатный период закончился.",
            f"Чтобы продолжить пользоваться дневником, нужна подписка на {duration_title}.",
        ]
        if trial_end_text:
            lines.insert(1, f"Триал закончился: {trial_end_text}")

        message = ft.Text(
            "\n".join(lines),
            size=14,
            color="#D7ECFF",
            text_align=ft.TextAlign.CENTER if hasattr(ft, "TextAlign") else None,
        )

        def _show_dialog(title_text: str, body_text: str):
            dialog = ft.AlertDialog(
                title=ft.Text(title_text),
                content=ft.Text(body_text),
                actions=[ft.TextButton("ОК", on_click=lambda _: _close_dialog())],
            )
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

        def _close_dialog():
            try:
                self.page.dialog.open = False
            except Exception:
                pass
            try:
                self.page.update()
            except Exception:
                pass

        def _go_main():
            if callable(self.on_back):
                self.on_back()
                return
            import main

            main.main(self.page)

        def _show_progress_dialog():
            try:
                content = ft.Column(
                    [
                        ft.ProgressRing(color="#2E86DE"),
                        ft.Container(height=12),
                        ft.Text("Создаём платёж...", size=14),
                        ft.Container(height=6),
                        ft.Text("Подождите 2–5 секунд.", size=12),
                    ],
                    spacing=0,
                )
            except Exception:
                content = ft.Text("Создаём платёж... Подождите.")

            dialog = ft.AlertDialog(
                title=ft.Text("Оплата"),
                content=content,
                actions=[ft.TextButton("ЗАКРЫТЬ", on_click=lambda _: _close_dialog())],
            )
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

        def _show_check_progress_dialog():
            try:
                content = ft.Column(
                    [
                        ft.ProgressRing(color="#2E86DE"),
                        ft.Container(height=12),
                        ft.Text("Проверяем оплату...", size=14),
                        ft.Container(height=6),
                        ft.Text("Подождите 2–5 секунд.", size=12),
                    ],
                    spacing=0,
                )
            except Exception:
                content = ft.Text("Проверяем оплату... Подождите.")

            dialog = ft.AlertDialog(
                title=ft.Text("Оплата"),
                content=content,
                actions=[ft.TextButton("ЗАКРЫТЬ", on_click=lambda _: _close_dialog())],
            )
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

        async def _launch_pay_url(url: str):
            if hasattr(self.page, "launch_url"):
                try:
                    result = self.page.launch_url(url)
                    if inspect.isawaitable(result):
                        await result
                    return
                except Exception:
                    pass
            try:
                __import__("webbrowser").open(url)
            except Exception:
                pass

        async def _pay_async():
            service = YooKassaService()
            if not service.is_configured():
                _close_dialog()
                _show_dialog("Оплата", "Оплата временно недоступна. Попробуйте позже.")
                return

            try:
                url = await service.create_payment(
                    user_id=user_id,
                    amount_rub=price_amount,
                    description=f"Workout Flow — доступ на {duration_title}",
                )
            except Exception:
                _close_dialog()
                _show_dialog("Оплата", "Не удалось создать платёж. Попробуйте позже.")
                return

            _close_dialog()

            try:
                await _launch_pay_url(url)
            except Exception:
                pass

            async def _open_pay_url_async():
                try:
                    await _launch_pay_url(url)
                except Exception:
                    pass

            def _open_pay_url(_):
                try:
                    if hasattr(self.page, "run_task"):
                        self.page.run_task(_open_pay_url_async)
                        return
                except Exception:
                    pass
                try:
                    __import__("webbrowser").open(url)
                except Exception:
                    pass

            def _copy_pay_url(_):
                try:
                    if hasattr(self.page, "set_clipboard"):
                        self.page.set_clipboard(url)
                        _show_dialog("Оплата", "Ссылка скопирована.")
                        return
                except Exception:
                    pass
                _show_dialog("Оплата", "Не удалось скопировать ссылку на этом устройстве. Скопируйте вручную из поля.")

            try:
                url_field = ft.TextField(
                    value=url,
                    read_only=True,
                    multiline=True,
                    min_lines=2,
                    max_lines=3,
                    text_size=12,
                    width=320,
                )
            except Exception:
                try:
                    url_field = ft.TextField(
                        value=url,
                        read_only=True,
                        multiline=True,
                        width=320,
                    )
                except Exception:
                    url_field = ft.Text(url, size=12)

            dialog = ft.AlertDialog(
                title=ft.Text("Оплата"),
                content=ft.Column(
                    [
                        ft.Text("Если страница оплаты не открылась автоматически, откройте её по ссылке:"),
                        ft.Container(height=8),
                        url_field,
                        ft.Container(height=8),
                        ft.TextButton("ОТКРЫТЬ ОПЛАТУ", on_click=_open_pay_url),
                        ft.TextButton("СКОПИРОВАТЬ ССЫЛКУ", on_click=_copy_pay_url),
                    ],
                    spacing=0,
                ),
                actions=[ft.TextButton("ЗАКРЫТЬ", on_click=lambda _: _close_dialog())],
            )
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

        def _pay(_):
            if hasattr(self.page, "run_task"):
                _show_progress_dialog()
                self.page.run_task(_pay_async)
            else:
                _show_dialog("Оплата", "Оплата в этом режиме недоступна. Откройте приложение в браузере.")

        def _check_paid(_):
            _show_check_progress_dialog()

            async def _check_paid_async():
                try:
                    allowed = await asyncio.wait_for(
                        asyncio.to_thread(self.subscription_service.is_access_allowed, device_id=user_id),
                        timeout=4,
                    )
                except Exception:
                    _close_dialog()
                    _show_dialog("Оплата", "Не удалось проверить оплату. Попробуйте ещё раз.")
                    return

                if allowed:
                    _close_dialog()
                    _go_main()
                    return

                _close_dialog()
                _show_dialog("Оплата", "Платёж ещё не подтверждён. Обычно это занимает 1–2 минуты. Попробуйте снова.")

            if hasattr(self.page, "run_task"):
                self.page.run_task(_check_paid_async)
                return

            try:
                _close_dialog()
            except Exception:
                pass

            try:
                if self.subscription_service.is_access_allowed(device_id=user_id):
                    _go_main()
                else:
                    _show_dialog("Оплата", "Платёж ещё не подтверждён. Обычно это занимает 1–2 минуты. Попробуйте снова.")
            except Exception:
                _show_dialog("Оплата", "Не удалось проверить оплату. Попробуйте ещё раз.")

        def _back(_):
            _go_main()

        if payment_mode == "test":
            pay_label = f"ОПЛАТИТЬ {int(price_amount)} ₽ (ТЕСТ)"
        else:
            if price_amount == int(price_amount):
                pay_label = f"ОПЛАТИТЬ {int(price_amount)} ₽"
            else:
                pay_label = f"ОПЛАТИТЬ {price_amount} ₽"

        pay_btn = ft.Container(
            content=ft.Text(pay_label, size=16, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            width=320,
            height=58,
            alignment=ft.alignment.center,
            bgcolor="#2563EB",
            border_radius=ft.border_radius.all(28),
            on_click=_pay,
        )

        check_btn = ft.Container(
            content=ft.Text("Я ОПЛАТИЛ", size=16, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            width=320,
            height=58,
            alignment=ft.alignment.center,
            bgcolor="#1F5FA9",
            border_radius=ft.border_radius.all(28),
            on_click=_check_paid,
        )

        back_btn = ft.Container(
            content=ft.Text("НАЗАД", size=16, weight=ft.FontWeight.W_600, color="#D7ECFF"),
            width=320,
            height=58,
            alignment=ft.alignment.center,
            bgcolor="#2B2F36",
            border_radius=ft.border_radius.all(28),
            on_click=_back,
        )

        layout = ft.Column(
            [
                ft.Container(height=40),
                ft.Container(alignment=ft.alignment.center, content=title),
                ft.Container(height=14),
                ft.Container(width=320, alignment=ft.alignment.center, content=message),
                ft.Container(height=20),
                ft.Container(alignment=ft.alignment.center, content=pay_btn),
                ft.Container(height=12),
                ft.Container(alignment=ft.alignment.center, content=check_btn),
                ft.Container(height=16),
                ft.Container(alignment=ft.alignment.center, content=back_btn),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.page.add(mobile_frame(layout))
        self.page.update()
