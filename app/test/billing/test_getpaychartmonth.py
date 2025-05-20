import pytest
from app.database import SessionLocal
from app.billing.services import BillingService

@pytest.fixture(scope="function")
def db_session():
    """Sesión real a la base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_payment_chart_month(db_session):
    # Instancia el servicio con la sesión real
    service = BillingService(db_session)

    # Año y mes que se usarán para prueba; usa un año y mes que sabes que hay pagos en la BD
    year = 2023
    month = 5

    # Ejecutar método
    result = service.get_payment_chart_month(year, month)

    # Validaciones básicas:
    assert isinstance(result, list), "Debe devolver una lista"
    if result:  # Si hay datos, verificar estructura
        for entry in result:
            assert "dia" in entry, "Cada entrada debe tener 'dia'"
            assert "total" in entry, "Cada entrada debe tener 'total'"
            assert isinstance(entry["dia"], int), "'dia' debe ser entero"
            assert isinstance(entry["total"], int), "'total' debe ser entero"

    # Opcional: Imprimir resultado para inspección manual
    print(f"Pagos en {year}-{month}: {result}")
