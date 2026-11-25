import base64
import os
import uuid
from decimal import Decimal

import httpx


class YooKassaService:
    API_URL = "https://api.yookassa.ru/v3/payments"

    def __init__(self):
        self.shop_id = (os.getenv("YOOKASSA_SHOP_ID") or "").strip()
        self.secret_key = (os.getenv("YOOKASSA_SECRET_KEY") or "").strip()
        self.return_url = (os.getenv("YOOKASSA_RETURN_URL") or "").strip()

    def _auth_header(self) -> str:
        raw = f"{self.shop_id}:{self.secret_key}".encode("utf-8")
        return "Basic " + base64.b64encode(raw).decode("ascii")

    def is_configured(self) -> bool:
        return bool(self.shop_id and self.secret_key and self.return_url)

    async def create_payment(self, user_id: str, amount_rub: Decimal, description: str) -> str:
        if not self.is_configured():
            raise RuntimeError("YOOKASSA_SHOP_ID/YOOKASSA_SECRET_KEY/YOOKASSA_RETURN_URL не настроены")

        user_id = (user_id or "").strip().lower() or "default"
        amount_str = f"{Decimal(amount_rub):.2f}"

        payload = {
            "amount": {"value": amount_str, "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": self.return_url},
            "capture": True,
            "description": description,
            "metadata": {"user_id": user_id},
        }

        headers = {
            "Authorization": self._auth_header(),
            "Idempotence-Key": str(uuid.uuid4()),
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(self.API_URL, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()

        confirmation = data.get("confirmation") or {}
        url = (confirmation.get("confirmation_url") or "").strip()
        if not url:
            raise RuntimeError("YooKassa не вернула confirmation_url")
        return url
