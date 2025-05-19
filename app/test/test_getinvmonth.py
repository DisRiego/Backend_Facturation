import pytest
from app.billing.services import BillingService
from app.database import SessionLocal

@pytest.fixture(scope="module")
def db_session():
    """Fixture para crear la sesión con SessionLocal."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_invoice_amount_month(db_session):
    billing_service = BillingService(db_session)

    # Ajusta estos valores según un año y mes que existan en tu base
    year = 2025
    month = 5

    total = billing_service.get_invoice_amount_month(year, month)

    # Verifica que retorne un float
    assert isinstance(total, float), "El total debe ser un float"

    # El total debe ser mayor o igual a cero (puede no haber facturas y sumar 0)
    assert total >= 0, "El total facturado no puede ser negativo"

    # Opcional: si sabes un valor esperado exacto, puedes comparar con ese
    # expected_total = 1234.56
    # assert total == expected_total, f"El total esperado es {expected_total}"
