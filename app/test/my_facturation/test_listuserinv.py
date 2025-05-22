import pytest
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.my_facturation.services import MyFacturationService
from app.payu.models import Invoice
from app.facturation.models import User, Lot, PropertyLot, PaymentInterval
from datetime import datetime, timedelta
import random

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(scope="function")
def test_user_with_invoice(db_session: Session):
    random_suffix = random.randint(10000, 99999)
    user = User(
        name=f"TestUser{random_suffix}",
        first_last_name="TestLastName1",
        second_last_name="TestLastName2",
        document_number=str(random_suffix)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Usar PaymentInterval existente con id=1
    interval = db_session.query(PaymentInterval).filter(PaymentInterval.id == 1).first()
    if not interval:
        raise Exception("No se encontró PaymentInterval con id=1 en la base de datos")

    lot = Lot(
        name=f"TestLot{random_suffix}",
        longitude=0.0,
        latitude=0.0,
        extension=1.0,
        real_estate_registration_number=random.randint(100000, 999999),
        payment_interval=interval,
        state_id=5
    )
    db_session.add(lot)
    db_session.commit()
    db_session.refresh(lot)
    db_session.refresh(lot)

    # Relacionar PropertyLot con propiedad dummy
    # Primero crear Property
    from app.facturation.models import Property
    prop = Property(
        name=f"TestProperty{random_suffix}",
        longitude=0.0,
        latitude=0.0,
        extension=1.0,
        real_estate_registration_number=random.randint(100000, 999999),
        State=3
    )
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)

    prop_lot = PropertyLot(property_id=prop.id, lot_id=lot.id)
    db_session.add(prop_lot)
    db_session.commit()

    # Crear factura asociada al usuario y lote
    invoice = Invoice(
        reference_code=f"REF{random_suffix}",
        client_name=f"TestClient{random_suffix}",
        client_email=f"testclient{random_suffix}@email.com",
        issuance_date=datetime.utcnow(),
        expiration_date=datetime.utcnow() + timedelta(days=30),
        invoiced_period="30",
        billing_start_date=datetime.utcnow() - timedelta(days=30),
        billing_end_date=datetime.utcnow(),
        total_amount=100.50,
        lot_id=lot.id,
        user_id=user.id,
        status="pendiente"
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)

    yield user, invoice


def test_list_user_invoices_success(db_session: Session, test_user_with_invoice):
    user, invoice = test_user_with_invoice
    service = MyFacturationService(db_session)

    result = service.list_user_invoices(user.id)

    assert isinstance(result, list)
    assert len(result) >= 1

    found_invoice = next((inv for inv in result if inv["invoice_id"] == invoice.id), None)
    assert found_invoice is not None
    assert found_invoice["reference_code"] == invoice.reference_code
    assert found_invoice["lot_id"] == invoice.lot_id
    assert found_invoice["total_amount"] == invoice.total_amount
    assert found_invoice["status"] == invoice.status
    assert "expiration_date" in found_invoice

def test_list_user_invoices_user_not_found(db_session: Session):
    service = MyFacturationService(db_session)

    with pytest.raises(Exception) as exc_info:
        service.list_user_invoices(99999999)  # ID muy alto para no existir

    assert "Usuario no encontrado" in str(exc_info.value)
