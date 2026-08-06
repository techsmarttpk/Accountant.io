"""Telegram bot entrypoint. Run as a separate process from the API
(see docker-compose.yml) — `python -m app.bot.main`.
"""

from __future__ import annotations

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.bot.api_client import BackendClient
from app.bot.handlers import handle_audio, handle_document, handle_text, start
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def _post_init(application: Application) -> None:
    settings = get_settings()
    application.bot_data["backend_client"] = BackendClient(settings)
    logger.info("bot_started", backend_base_url=settings.backend_base_url)


async def _post_shutdown(application: Application) -> None:
    client: BackendClient | None = application.bot_data.get("backend_client")
    if client is not None:
        await client.close()


def build_application() -> Application:
    settings = get_settings()
    configure_logging(settings)

    if not settings.telegram_bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. Configure it via environment variable "
            "or .env — it must never be hardcoded in source."
        )

    application = (
        Application.builder()
        .token(settings.telegram_bot_token.get_secret_value())
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return application


def main() -> None:
    application = build_application()
    application.run_polling()


if __name__ == "__main__":
    main()
