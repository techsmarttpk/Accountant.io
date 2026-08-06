"""Thin HTTP client the bot uses to talk to the backend API.

Deliberately contains zero tax/extraction/RAG logic — every method is a
direct pass-through to an endpoint. This is what "the bot is a client, not
where the product lives" means concretely: delete this file and rewrite it
in a different language/framework tomorrow, and the product is unaffected.
"""

from __future__ import annotations

import httpx

from app.core.config import Settings


class BackendApiError(Exception):
    def __init__(self, status_code: int, error_code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message


class BackendClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.backend_base_url.rstrip("/") + settings.api_v1_prefix
        self._api_key = settings.internal_api_key.get_secret_value()
        self._client = httpx.AsyncClient(timeout=60.0)

    def _headers(self, telegram_user_id: int) -> dict:
        return {
            "X-Internal-Api-Key": self._api_key,
            "X-Telegram-User-Id": str(telegram_user_id),
        }

    async def _raise_for_app_error(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        try:
            body = response.json()
        except ValueError:
            body = {}
        raise BackendApiError(
            status_code=response.status_code,
            error_code=body.get("error_code", "unknown_error"),
            message=body.get("message", "The backend returned an error."),
        )

    async def calculate_from_text(
        self, telegram_user_id: int, text: str, *, financial_year: str, regime: str
    ) -> dict:
        response = await self._client.post(
            f"{self._base_url}/calculations",
            headers=self._headers(telegram_user_id),
            json={"text": text, "financial_year": financial_year, "regime": regime},
        )
        await self._raise_for_app_error(response)
        return response.json()

    async def calculate_from_audio(
        self,
        telegram_user_id: int,
        filename: str,
        content: bytes,
        *,
        financial_year: str,
        regime: str,
    ) -> dict:
        response = await self._client.post(
            f"{self._base_url}/calculations/from-audio",
            headers=self._headers(telegram_user_id),
            files={"file": (filename, content, "audio/ogg")},
            data={"financial_year": financial_year, "regime": regime},
        )
        await self._raise_for_app_error(response)
        return response.json()

    async def upload_document_and_calculate(
        self,
        telegram_user_id: int,
        filename: str,
        content: bytes,
        *,
        financial_year: str,
        regime: str,
    ) -> dict:
        upload_response = await self._client.post(
            f"{self._base_url}/documents",
            headers=self._headers(telegram_user_id),
            files={"file": (filename, content, "application/pdf")},
        )
        await self._raise_for_app_error(upload_response)
        document = upload_response.json()

        calc_response = await self._client.post(
            f"{self._base_url}/calculations",
            headers=self._headers(telegram_user_id),
            json={
                "financial_year": financial_year,
                "regime": regime,
                "document_id": document["id"],
            },
        )
        await self._raise_for_app_error(calc_response)
        return calc_response.json()

    async def ask(self, telegram_user_id: int, question: str) -> dict:
        response = await self._client.post(
            f"{self._base_url}/chat",
            headers=self._headers(telegram_user_id),
            json={"question": question},
        )
        await self._raise_for_app_error(response)
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
