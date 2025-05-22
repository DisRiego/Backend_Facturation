import pytest
import random
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.facturation.services import InvoiceService
from app.payu.models import Invoice, Payment
from app.facturation.models import Lot
from app.database import SessionLocal

@pytest.fixture(scope="module")
def sessionlocal():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def dbsession(sessionlocal: Session):
    yield sessionlocal
    # No hacemos rollback para preservar datos entre pruebas si se desea

@pytest.fixture(scope="function")
def setup_invoice_and_related(dbsession: Session):
    lot_id = random.randint(1000, 9999)
    invoice_id = random.randint(10000, 99999)
    payment_id = random.randint(10000, 99999)
    real_estate_registration_number = random.randint(100000, 999999)

    # Crear lote
    lot = Lot(
        id=lot_id,
        name="Lote Test",
        longitude=1.0,
        latitude=1.0,
        extension=10.0,
        real_estate_registration_number=real_estate_registration_number,
        payment_interval_id=1,
        state_id=5,
        type_crop_id=1
    )
    dbsession.add(lot)
    dbsession.commit()

    # Crear factura
    invoice = Invoice(
        id=invoice_id,
        reference_code=f"INV-TEST-{invoice_id}",
        client_name="Cliente Prueba",
        client_email="cliente@prueba.com",
        issuance_date=datetime.utcnow(),
        expiration_date=datetime.utcnow() + timedelta(days=30),
        invoiced_period=30,
        billing_start_date=datetime.utcnow() - timedelta(days=30),
        billing_end_date=datetime.utcnow(),
        total_amount=1000.0,
        lot_id=lot.id,
        status="pendiente",
        dian_status="aceptada",
        pdf_url="http://test.pdf",
        xml_url="http://test.xml",
        factus_number=f"FCT-{invoice_id}",
        payload={},  # Campo JSON no nulo, colocar diccionario vacío
    )
    dbsession.add(invoice)
    dbsession.commit()

    # Crear pago asociado
    payment = Payment(
        id=payment_id,
        invoice_id=invoice.id,
        reference_code=f"PAY-REF-{payment_id}",
        transaction_id=f"TX-{payment_id}",
        payment_method="PSE",
        status="Aprobado",
        amount=1000.0,
        currency="COP",
        payer_email="pagador@prueba.com",
        paid_at=datetime.utcnow()
    )
    dbsession.add(payment)
    dbsession.commit()

    yield invoice, payment, lot

    # Opcional: limpiar datos al finalizar (si deseas eliminar, descomenta)
    # dbsession.delete(payment)
    # dbsession.delete(invoice)
    # dbsession.delete(lot)
    # dbsession.commit()


def test_get_invoice_detail_success(dbsession: Session, setup_invoice_and_related):
    invoice, payment, lot = setup_invoice_and_related
    service = InvoiceService(dbsession)

    response = service.get_invoice_detail(invoice.id)

    # response es un dict con clave "invoice", "payment", "concepts"
    assert isinstance(response, dict)
    assert "invoice" in response
    assert response["invoice"]["client_name"] == "Cliente Prueba"
    assert response["invoice"]["reference_code"] == f"INV-TEST-{invoice.id}"
    assert response["invoice"]["total_amount"] == 1000.0
    assert response["invoice"]["lot_id"] == lot.id

    assert "payment" in response
    assert response["payment"] is not None
    assert response["payment"]["reference_code"] == f"PAY-REF-{payment.id}"

def test_get_invoice_detail_not_found(dbsession: Session):
    service = InvoiceService(dbsession)

    fake_id = 99999999
    with pytest.raises(HTTPException) as exc_info:
        service.get_invoice_detail(fake_id)
    assert exc_info.value.status_code == 404
    assert "Factura no encontrada" in exc_info.value.detail
