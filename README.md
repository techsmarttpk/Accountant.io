# Accountant.io

A fintech document assistant: Telegram bot + FastAPI backend for Indian
income-tax estimation from text, PDF documents, or voice notes, plus a
retrieval-grounded Q&A assistant over a tax-law knowledge base.

## Architecture

```
app/
  core/        settings, logging, exceptions, auth
  db/          SQLAlchemy models, async session, migrations live in alembic/
  repositories/ data access, one per aggregate
  services/
    tax_engine/   versioned Indian tax slab rules + pure calculator
    extraction/   PDF/OCR/audio -> text -> structured financial fields
    rag/          knowledge base retrieval + grounded answer generation
  api/v1/      FastAPI routers (thin — delegate to services)
  bot/         Telegram bot; a pure HTTP client of the API, no business logic
```

The bot and API are separate processes (see `docker-compose.yml`) so the
API can be used by any future client (web, mobile) without touching bot code.

## Running locally (no Docker)

```
pip install -r requirements-dev.txt
cp .env.example .env   # fill in INTERNAL_API_KEY and TELEGRAM_BOT_TOKEN
alembic upgrade head
uvicorn app.main:app --reload          # terminal 1
python -m app.bot.main                 # terminal 2
```

## Running with Docker

```
cp .env.example .env
docker compose up --build
```

## Tests

```
pytest --cov=app
```

## Known scope limitations (tracked, not accidental)

- Tax calculation covers salaried-employee scenarios with the fields the
  extractor recognizes (`app/services/extraction/financial_field_extractor.py`);
  it does not yet model HRA exemption, capital gains, or business income.
- RAG retrieval uses TF-IDF, not dense embeddings — a deliberate trade-off
  for a small, curated knowledge base (see
  `app/services/rag/embedding_provider.py` for the reasoning and upgrade path).
- Answer generation is extractive (returns cited source passages verbatim)
  rather than free-form LLM generation, since no LLM API key is configured
  in this environment (see `app/services/rag/generation_provider.py`).
- Speech-to-text defaults to the free Google Web Speech API for zero-setup
  local development; swap `STT_PROVIDER=whisper` and implement
  `WhisperProvider` before handling production audio volume.
