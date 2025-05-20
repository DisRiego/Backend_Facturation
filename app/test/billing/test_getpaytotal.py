# test_billing_service.py
import pytest
from app.database import SessionLocal
from app.billing.services import BillingService
from datetime import datetime

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_payment_totals(db_session):
    service = BillingService(db_session)

    now = datetime.utcnow()
    year = now.year
    month = now.month

    result = service.get_payment_totals(year, month)

    # Validar que el resultado es un dict con las claves esperadas
    expected_keys = {
        "ingresos_totales",
        "ingresos_anuales",
        "ingresos_mensuales",
        "tasa_rechazo"
    }
    assert isinstance(result, dict)
    assert expected_keys.issubset(result.keys())

    # Validar que los valores sean float o int y tengan sentido
    assert isinstance(result["ingresos_totales"], float)
    assert result["ingresos_totales"] >= 0

    assert isinstance(result["ingresos_anuales"], float)
    assert result["ingresos_anuales"] >= 0

    assert isinstance(result["ingresos_mensuales"], float)
    assert result["ingresos_mensuales"] >= 0

    assert isinstance(result["tasa_rechazo"], float)
    # tasa de rechazo puede ser 0 hasta 100%
    assert 0 <= result["tasa_rechazo"] <= 100

    # Opcional: si quieres imprimir para debug (quitar en producción)
    print(f"Pago Totales {year}-{month}: {result}")
