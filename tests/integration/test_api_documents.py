import fitz


def _make_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    content = doc.tobytes()
    doc.close()
    return content


async def test_upload_pdf_and_calculate_from_document_id(client, auth_headers):
    pdf_bytes = _make_pdf_bytes("Salary: 900000\n80C: 100000\nRent Paid: 180000")

    upload = await client.post(
        "/api/v1/documents",
        headers=auth_headers(),
        files={"file": ("payslip.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["extraction_status"] == "success"
    document_id = body["id"]

    calc = await client.post(
        "/api/v1/calculations",
        headers=auth_headers(),
        json={"document_id": document_id, "financial_year": "2024-25", "regime": "new"},
    )
    assert calc.status_code == 201
    assert calc.json()["extracted_fields"]["salary"] == 900_000


async def test_upload_rejects_non_pdf_content_type(client, auth_headers):
    r = await client.post(
        "/api/v1/documents",
        headers=auth_headers(),
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 415
    assert r.json()["error_code"] == "unsupported_file_type"


async def test_calculation_from_unknown_document_id_is_not_found(client, auth_headers):
    import uuid

    r = await client.post(
        "/api/v1/calculations",
        headers=auth_headers(),
        json={"document_id": str(uuid.uuid4()), "financial_year": "2024-25", "regime": "new"},
    )
    assert r.status_code == 404
