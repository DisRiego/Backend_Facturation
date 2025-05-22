import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError
from datetime import datetime, timedelta
from app.main import app
from app.database import SessionLocal
from app.payu.models import Invoice
from app.facturation.models import User, Lot, Property, PropertyLot, PropertyUser
from app.facturation.services import InvoiceService

@pytest.fixture(scope="module")
def sessionlocal():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def db_session(sessionlocal: Session):
    yield sessionlocal
    sessionlocal.rollback()

@pytest.fixture
def invoice_service(db_session: Session):
    return InvoiceService(db_session)

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
        
@pytest.fixture
def test_user(db_session: Session):
    user = db_session.query(User).filter(User.document_number == "123456789").first()
    if not user:
        user = User(
            name="Test",
            first_last_name="User",
            second_last_name="Uno",
            document_number="123456789"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    yield user
    # Limpieza segura
    try:
        if user.document_number == "123456789":
            db_session.delete(user)
            db_session.commit()
    except ObjectDeletedError:
        db_session.rollback()

@pytest.fixture
def test_property_and_lot(db_session: Session, test_user: User):
    property = Property(
        name="Test Property",
        longitude=10.0,
        latitude=10.0,
        extension=100.0,
        real_estate_registration_number=12345,
        State=3
    )
    db_session.add(property)
    db_session.commit()
    db_session.refresh(property)

    lot = Lot(
        name="Test Lot",
        longitude=10.0,
        latitude=10.0,
        extension=50.0,
        real_estate_registration_number=54321,
        payment_interval_id=1,
        state_id=5,
        type_crop_id=1
    )
    db_session.add(lot)
    db_session.commit()
    db_session.refresh(lot)

    prop_lot = PropertyLot(property_id=property.id, lot_id=lot.id)
    db_session.add(prop_lot)

    prop_user = PropertyUser(property_id=property.id, user_id=test_user.id)
    db_session.add(prop_user)
    db_session.commit()

    yield lot

    # Limpieza segura
    try:
        db_session.delete(prop_user)
        db_session.delete(prop_lot)
        db_session.delete(lot)
        db_session.delete(property)
        db_session.commit()
    except ObjectDeletedError:
        db_session.rollback()

def test_create_invoice_success(db_session: Session, invoice_service: InvoiceService, test_property_and_lot: Lot):
    # Limpia facturas previas para evitar error 400
    invoices_exist = db_session.query(Invoice).filter(Invoice.lot_id == test_property_and_lot.id).all()
    for inv in invoices_exist:
        db_session.delete(inv)
    db_session.commit()

    payment_data = {
        "lot_id": test_property_and_lot.id
    }

    response = invoice_service.create_invoice(payment_data=payment_data)

    assert response.status_code == 200

    invoice = db_session.query(Invoice).filter(Invoice.lot_id == test_property_and_lot.id).order_by(Invoice.id.desc()).first()
    assert invoice is not None
    assert invoice.status == "pendiente"

    # Limpieza factura creada
    db_session.delete(invoice)
    db_session.commit()
