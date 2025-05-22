import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_list_payments_general(client, db_session):
    """
    Test para verificar la respuesta del endpoint /billing/payments/general
    """

    response = client.get("/billing/payments/general")
    assert response.status_code == 200

    json_data = response.json()

    assert "success" in json_data
    assert json_data["success"] is True
    assert "data" in json_data
    assert isinstance(json_data["data"], list)

    if len(json_data["data"]) > 0:
        item = json_data["data"][0]
        expected_keys = {
            "invoice_number",
            "payer_document",
            "payment_date",
            "reference_code",
            "payment_method",
            "paid_amount",
            "payment_status_id",
            "payment_status_name",
        }
        assert expected_keys.issubset(item.keys())

        # Validar tipos básicos
        assert isinstance(item["invoice_number"], (str, type(None)))
        assert isinstance(item["payer_document"], (str, int, type(None)))
        assert isinstance(item["payment_date"], (str, type(None)))
        assert isinstance(item["paid_amount"], (float, int))

        # Validar que payment_status_name sea texto
        assert isinstance(item["payment_status_name"], str)

        # payment_status_id puede ser texto o entero
        assert isinstance(item["payment_status_id"], ( str))
