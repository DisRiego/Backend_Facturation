import random
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.facturation.models import Property, Lot, PropertyLot, PropertyUser
from app.payu.models import Invoice
from sqlalchemy.orm import Session

@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
        db.rollback()
    finally:
        db.close()

def create_property(db: Session) -> Property:
    real_estate_number = random.randint(100000, 999999)
    prop = Property(
        name="Propiedad Test",
        longitude=-75.3,
        latitude=2.9,
        extension=1000,
        real_estate_registration_number=real_estate_number,
        State=3
    )
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop

def create_lot(db: Session) -> Lot:
    real_estate_number = random.randint(100000, 999999)
    lot = Lot(
        name="Lote Test",
        longitude=-75.3,
        latitude=2.9,
        extension=1000,
        real_estate_registration_number=real_estate_number,
        payment_interval=1,
        State=5
    )
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot

def create_property_lot(db: Session, property_id: int, lot_id: int) -> PropertyLot:
    prop_lot = PropertyLot(property_id=property_id, lot_id=lot_id)
    db.add(prop_lot)
    db.commit()
    db.refresh(prop_lot)
    return prop_lot

def create_property_user(db: Session, property_id: int, user_id: int) -> PropertyUser:
    prop_user = PropertyUser(property_id=property_id, user_id=user_id)
    db.add(prop_user)
    db.commit()
    db.refresh(prop_user)
    return prop_user

def create_invoice(db: Session, lot_id: int, user_id: int) -> Invoice:
    invoice = Invoice(
        reference_code=f"TEST-{random.randint(1000,9999)}",
        user_id=user_id,
        client_name="Test User",
        client_email="testuser@example.com",
        billing_start_date="2025-01-01",
        billing_end_date="2025-01-31",
        issuance_date="2025-02-01",
        expiration_date="2025-02-15",
        invoiced_period="30",
        total_amount=100.0,
        lot_id=lot_id,
        status="pendiente"
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice

client = TestClient(app)

@pytest.mark.usefixtures("db_session")
def test_create_pse_payment_success(db_session):
    user_id = 6

    prop = create_property(db_session)
    lot = create_lot(db_session)
    create_property_lot(db_session, prop.id, lot.id)
    create_property_user(db_session, prop.id, user_id)  # <--- Asociar usuario al predio

    invoice = create_invoice(db_session, lot.id, user_id)

    payment_data = {
        "detailInvoice": {"invoice_id": invoice.id},
        "bankCode": "12345",
        "deviceSessionId": "device-session-xyz",
        "ipAddress": "127.0.0.1",
        "cookie": "cookie-data",
        "userAgent": "test-agent"
    }

    from app.payu.services import PayUService
    payu_service = PayUService(db_session)
    response = payu_service.create_pse_payment(payment_data)

    # Imprime respuesta en caso de error para depuración
    if response.status_code != 200:
        print(response.body.decode())

    assert response.status_code == 200
    content = response.body.decode()
    assert "success" in content

@pytest.mark.usefixtures("db_session")
def test_create_pse_payment_already_paid(db_session):
    user_id = 6

    prop = create_property(db_session)
    lot = create_lot(db_session)
    create_property_lot(db_session, prop.id, lot.id)
    create_property_user(db_session, prop.id, user_id)

    invoice = Invoice(
        reference_code=f"TEST-{random.randint(1000,9999)}",
        user_id=user_id,
        client_name="Test User",
        client_email="testuser@example.com",
        billing_start_date="2025-01-01",
        billing_end_date="2025-01-31",
        issuance_date="2025-02-01",
        expiration_date="2025-02-15",
        invoiced_period="30",
        total_amount=100.0,
        lot_id=lot.id,
        status="pagada"
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)

    payment_data = {
        "detailInvoice": {"invoice_id": invoice.id},
        "bankCode": "12345",
        "deviceSessionId": "device-session-xyz",
        "ipAddress": "127.0.0.1",
        "cookie": "cookie-data",
        "userAgent": "test-agent"
    }

    from app.payu.services import PayUService
    payu_service = PayUService(db_session)
    response = payu_service.create_pse_payment(payment_data)

    if response.status_code != 400:
        print(response.body.decode())

    assert response.status_code == 400
    content = response.body.decode()
    assert "La factura ya fue pagada" in content
