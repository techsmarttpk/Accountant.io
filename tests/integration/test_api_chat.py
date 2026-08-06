async def test_chat_returns_grounded_answer_with_sources(client, auth_headers):
    r = await client.post(
        "/api/v1/chat",
        headers=auth_headers(),
        json={"question": "What deductions can I claim under Section 80C?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["grounded"] is True
    assert len(body["sources"]) > 0


async def test_chat_does_not_hallucinate_on_out_of_domain_question(client, auth_headers):
    r = await client.post(
        "/api/v1/chat",
        headers=auth_headers(),
        json={"question": "What's the best recipe for lasagna?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["grounded"] is False
    assert body["sources"] == []
