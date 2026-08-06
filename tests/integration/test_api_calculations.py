import pytest


async def test_health_requires_no_auth(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_protected_route_without_api_key_is_unauthorized(client):
    r = await client.get("/api/v1/users/me", headers={"X-Telegram-User-Id": "1"})
    assert r.status_code == 401
    assert r.json()["error_code"] == "unauthorized"


async def test_create_calculation_from_text(client, auth_headers):
    r = await client.post(
        "/api/v1/calculations",
        headers=auth_headers(),
        json={"text": "Salary: 1200000, 80C: 150000, Rent Paid: 240000", "financial_year": "2024-25", "regime": "new"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["total_income"] == 1_200_000
    assert body["rule_set_version"] == "IN-2024-25-NEW"
    assert body["total_payable"] > 0


async def test_calculation_with_no_recognizable_fields_is_rejected_not_zeroed(client, auth_headers):
    r = await client.post(
        "/api/v1/calculations",
        headers=auth_headers(),
        json={"text": "hi, just saying hello", "financial_year": "2024-25", "regime": "new"},
    )
    assert r.status_code == 422
    assert r.json()["error_code"] == "insufficient_financial_data"


async def test_calculation_requires_text_or_document_id(client, auth_headers):
    r = await client.post(
        "/api/v1/calculations",
        headers=auth_headers(),
        json={"financial_year": "2024-25", "regime": "new"},
    )
    assert r.status_code == 422


async def test_calculation_history_is_scoped_per_user(client, auth_headers):
    await client.post(
        "/api/v1/calculations",
        headers=auth_headers(telegram_user_id=1),
        json={"text": "Salary: 500000", "financial_year": "2024-25", "regime": "new"},
    )
    await client.post(
        "/api/v1/calculations",
        headers=auth_headers(telegram_user_id=2),
        json={"text": "Salary: 600000", "financial_year": "2024-25", "regime": "new"},
    )

    r1 = await client.get("/api/v1/calculations", headers=auth_headers(telegram_user_id=1))
    r2 = await client.get("/api/v1/calculations", headers=auth_headers(telegram_user_id=2))

    assert len(r1.json()) == 1
    assert len(r2.json()) == 1
    assert r1.json()[0]["total_income"] == 500_000
    assert r2.json()[0]["total_income"] == 600_000
