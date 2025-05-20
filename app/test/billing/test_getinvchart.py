import pytest
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.billing.services import BillingService

@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def test_get_invoice_chart_year(db_session: Session):
    service = BillingService(db_session)
    
    # Escoge un año actual o pasado; aquí tomo 2024 como ejemplo,
    # Cambia el año según los datos de tu base para asegurar que haya datos.
    test_year = 2024

    result = service.get_invoice_chart_year(test_year)

    # Debe ser lista
    assert isinstance(result, list)

    # Si hay datos, validar estructura y orden
    if len(result) > 0:
        # Validar que cada elemento es dict con claves 'mes' y 'total'
        for item in result:
            assert isinstance(item, dict)
            assert "mes" in item
            assert "total" in item
            assert isinstance(item["mes"], int)
            assert 1 <= item["mes"] <= 12
            assert isinstance(item["total"], int)
            assert item["total"] >= 0

        # Validar que los meses estén ordenados ascendentemente
        meses = [item["mes"] for item in result]
        assert meses == sorted(meses)
