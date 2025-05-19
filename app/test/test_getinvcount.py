import pytest
from sqlalchemy.orm import Session
from app.billing.services import BillingService

@pytest.fixture(scope="module")
def db_session():
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_invoice_counts(db_session: Session):
    service = BillingService(db_session)

    emitidas, pagadas, pendientes, vencidas = service.get_invoice_counts()

    # Validar que los conteos sean enteros y mayores o iguales a cero
    assert isinstance(emitidas, int) and emitidas >= 0
    assert isinstance(pagadas, int) and pagadas >= 0
    assert isinstance(pendientes, int) and pendientes >= 0
    assert isinstance(vencidas, int) and vencidas >= 0

    # Validar que el total emitidas sea mayor o igual a la suma de las otras categorías (pagadas + pendientes + vencidas)
    assert emitidas >= pagadas + pendientes + vencidas

    print(f"Facturas emitidas: {emitidas}")
    print(f"Facturas pagadas: {pagadas}")
    print(f"Facturas pendientes: {pendientes}")
    print(f"Facturas vencidas: {vencidas}")
