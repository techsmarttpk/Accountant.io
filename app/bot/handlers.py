"""Telegram update handlers.

Every handler's job is: pull data out of the Telegram `Update`, call the
backend over HTTP, format the reply. No PDF/OCR/regex/tax-math/RAG code
belongs here — that's what `app.bot.api_client.BackendClient` and the
FastAPI service exist for.
"""

from __future__ import annotations

import re

from telegram import Update
from telegram.ext import ContextTypes

from app.bot.api_client import BackendApiError, BackendClient
from app.core.logging import get_logger
from app.services.tax_engine.rules import DEFAULT_FINANCIAL_YEAR

logger = get_logger(__name__)

DEFAULT_REGIME = "new"

# Messages that look like a free-text tax question rather than a
# structured "Salary: X, 80C: Y" style submission get routed to RAG chat
# instead of the calculator. This is a stricter, less accident-prone
# version of the legacy single regex — it requires a question mark or an
# interrogative opener, rather than merely the *absence* of a few keywords.
_QUESTION_PATTERN = re.compile(
    r"\?\s*$|^(what|how|why|when|can|does|is|are|should)\b", re.IGNORECASE
)


def _client(context: ContextTypes.DEFAULT_TYPE) -> BackendClient:
    return context.bot_data["backend_client"]


def _format_calculation(result: dict) -> str:
    fields = ", ".join(f"{k}: ₹{v:,.0f}" for k, v in result["extracted_fields"].items())
    return (
        f"📊 Tax estimate ({result['financial_year']}, {result['regime']} regime)\n\n"
        f"Recognized fields: {fields or 'none'}\n"
        f"Taxable income: ₹{result['taxable_income']:,.2f}\n"
        f"Tax before rebate: ₹{result['tax_before_rebate']:,.2f}\n"
        f"Rebate applied: ₹{result['rebate_applied']:,.2f}\n"
        f"Cess (4%): ₹{result['cess']:,.2f}\n"
        f"Total payable: ₹{result['total_payable']:,.2f}\n\n"
        f"Rule set: {result['rule_set_version']}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to Accountant.io. Send your income/deduction details as "
        "text (e.g. 'Salary: 900000, 80C: 100000'), upload a PDF, send a "
        "voice note, or ask a tax question directly."
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    if not document:
        return

    telegram_file = await document.get_file()
    content = bytes(await telegram_file.download_as_bytearray())

    await update.message.reply_text("Document received, processing...")
    try:
        result = await _client(context).upload_document_and_calculate(
            update.effective_user.id,
            document.file_name or "upload.pdf",
            content,
            financial_year=DEFAULT_FINANCIAL_YEAR,
            regime=DEFAULT_REGIME,
        )
        await update.message.reply_text(_format_calculation(result))
    except BackendApiError as exc:
        await update.message.reply_text(f"Couldn't process that document: {exc.message}")
    except Exception:
        logger.error("handle_document_failed", exc_info=True)
        await update.message.reply_text("Something went wrong processing that document.")


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    audio = update.message.voice or update.message.audio
    if not audio:
        return

    telegram_file = await audio.get_file()
    content = bytes(await telegram_file.download_as_bytearray())

    await update.message.reply_text("Voice note received, transcribing...")
    try:
        result = await _client(context).calculate_from_audio(
            update.effective_user.id,
            "voice.ogg",
            content,
            financial_year=DEFAULT_FINANCIAL_YEAR,
            regime=DEFAULT_REGIME,
        )
        await update.message.reply_text(_format_calculation(result))
    except BackendApiError as exc:
        await update.message.reply_text(f"Couldn't process that recording: {exc.message}")
    except Exception:
        logger.error("handle_audio_failed", exc_info=True)
        await update.message.reply_text("Something went wrong processing that recording.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or ""
    client = _client(context)
    telegram_user_id = update.effective_user.id

    if _QUESTION_PATTERN.search(text.strip()):
        try:
            answer = await client.ask(telegram_user_id, text)
            reply = answer["answer"]
            if answer["sources"]:
                cites = ", ".join(sorted({s["source"] for s in answer["sources"]}))
                reply += f"\n\n(sources: {cites})"
            await update.message.reply_text(reply)
        except BackendApiError as exc:
            await update.message.reply_text(f"Couldn't answer that: {exc.message}")
        return

    try:
        result = await client.calculate_from_text(
            telegram_user_id, text, financial_year=DEFAULT_FINANCIAL_YEAR, regime=DEFAULT_REGIME
        )
        await update.message.reply_text(_format_calculation(result))
    except BackendApiError as exc:
        await update.message.reply_text(exc.message)
    except Exception:
        logger.error("handle_text_failed", exc_info=True)
        await update.message.reply_text("Something went wrong computing that.")
