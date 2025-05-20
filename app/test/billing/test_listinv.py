import pytest
from sqlalchemy.orm import Session
from app.billing.services import BillingService
from app.payu.models import Invoice
from app.database import SessionLocal

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture para obtener sesión DB limpia usando SessionLocal.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def test_list_invoices(db_session: Session):
    service = BillingService(db_session)

    # Llamar sin parámetros (offset=0, limit=100)
    invoices = service.list_invoices()

    # Validar que es lista
    assert isinstance(invoices, list)

    # Validar que no retorna más de 100
    assert len(invoices) <= 100

    if len(invoices) > 1:
        # Validar que está ordenado descendentemente por issuance_date
        fechas = [inv.issuance_date for inv in invoices]
        assert fechas == sorted(fechas, reverse=True)

    # Validar que cada elemento es instancia de Invoice
    for inv in invoices:
        assert isinstance(inv, Invoice)
        # Validar que tiene atributos esperados
        assert hasattr(inv, "reference_code")
        assert hasattr(inv, "issuance_date")
        assert hasattr(inv, "status")

    # Probar paginación con limit y offset
    invoices_offset = service.list_invoices(offset=1, limit=5)
    assert isinstance(invoices_offset, list)
    assert len(invoices_offset) <= 5

    # Si hay más de 5 facturas en total, paginación debe traer distinto resultado que la primera
    if len(invoices) > 5:
        assert invoices_offset[0].id != invoices[0].id
