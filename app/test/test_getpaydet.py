import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.billing.services import BillingService
from app.payu.models import Payment

@pytest.fixture(scope="module")
def db_session():
    """Crea y cierra la sesión con la base de datos para las pruebas"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client():
    """Test client para hacer peticiones HTTP"""
    with TestClient(app) as c:
        yield c

def test_get_payment_detail_success(db_session, client):
    """
    Prueba que el endpoint /billing/payments/{payment_id} devuelva
    correctamente los datos de un pago existente.
    """
    # 1. Buscar un payment_id existente en la base de datos
    payment = db_session.query(Payment).first()
    assert payment is not None, "No hay pagos en la base de datos para probar"

    payment_id = payment.id

    # 2. Hacer petición GET al endpoint
    response = client.get(f"/billing/payments/{payment_id}")
    assert response.status_code == 200

    data = response.json()
    assert data.get("success") is True
    assert "data" in data

    detail = data["data"]

    # 3. Validar que las llaves del diccionario coincidan con las esperadas
    expected_keys = {
        "payment_method",
        "payer_name",
        "transaction_amount",
        "payment_status_id",
        "payment_status_name",
        "payment_date",
        "reference_code",
        "payer_email",
    }
    assert expected_keys.issubset(detail.keys())

    # 4. Validar algunos tipos básicos (ejemplo)
    assert isinstance(detail["payment_method"], (str, type(None)))
    assert isinstance(detail["payer_name"], (str, type(None)))
    assert isinstance(detail["transaction_amount"], float)
    assert isinstance(detail["payment_status_id"], str)
    assert isinstance(detail["payment_status_name"], str)
    assert isinstance(detail["payment_date"], (str, type(None)))  # formato ISO
    assert isinstance(detail["reference_code"], (str, type(None)))
    assert isinstance(detail["payer_email"], (str, type(None)))

def test_get_payment_detail_not_found(client):
    """
    Prueba que se devuelva un error 404 al pedir un pago no existente.
    """
    invalid_payment_id = 999999999  # ID que seguramente no existe

    response = client.get(f"/billing/payments/{invalid_payment_id}")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Pago no encontrado"
