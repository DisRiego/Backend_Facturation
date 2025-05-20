import pytest
from sqlalchemy.orm import Session
from app.billing.services import BillingService
from app.database import SessionLocal

@pytest.fixture(scope="module")
def db_session() -> Session:
    """Fixture que crea una sesión real de base de datos para pruebas."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_payment_chart_year(db_session: Session):
    service = BillingService(db_session)
    
    # Elegimos un año para test; se recomienda usar un año conocido con pagos en BD
    year = 2023  # Ajusta según datos en BD
    
    result = service.get_payment_chart_year(year)
    
    # Validamos que devuelva una lista
    assert isinstance(result, list)
    
    # Validamos que cada elemento tenga 'mes' y 'total'
    for entry in result:
        assert "mes" in entry
        assert "total" in entry
        
        # mes debe ser entero entre 1 y 12
        assert isinstance(entry["mes"], int)
        assert 1 <= entry["mes"] <= 12
        
        # total debe ser entero >= 0
        assert isinstance(entry["total"], int)
        assert entry["total"] >= 0
    
    # Validar que la lista esté ordenada por mes ascendente
    meses = [entry["mes"] for entry in result]
    assert meses == sorted(meses)
