import pytest
import random
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.facturation.services import InvoiceService
from app.payu.models import Invoice, Payment
from app.facturation.models import Lot
from app.main import app
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
    # No rollback para preservar datos

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

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
        invoiced_period="2025-05",
        billing_start_date=datetime.utcnow() - timedelta(days=30),
        billing_end_date=datetime.utcnow(),
        total_amount=1000.0,
        lot_id=lot.id,
        status="pendiente",
        dian_status="aceptada",
        pdf_url="http://test.pdf",
        xml_url="http://test.xml",
        factus_number=f"FCT-{invoice_id}"
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

   

def test_get_invoice_detail_success(dbsession: Session, setup_invoice_and_related):
    invoice, payment, lot = setup_invoice_and_related
    service = InvoiceService(dbsession)

    response = service.get_invoice_detail(invoice.id)

    assert response.status_code == 200
    content = response.body.decode()
    assert "Cliente Prueba" in content
    assert f"INV-TEST-{invoice.id}" in content
    assert f"PAY-REF-{payment.id}" in content
    assert str(invoice.total_amount) in content
    assert str(lot.id) in content

def test_get_invoice_detail_not_found(dbsession: Session):
    service = InvoiceService(dbsession)

    fake_id = 99999999
    response = service.get_invoice_detail(fake_id)

    assert response.status_code == 404
    content = response.body.decode()
    assert "Factura no encontrada" in content


