import random
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.main import app
from app.database import SessionLocal
from app.facturation.services import InvoiceService
from app.facturation.models import User, Property, Lot, PropertyLot, PropertyUser

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
    # Opcional: limpiar si quieres
    # sessionlocal.rollback()

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def setup_data(dbsession: Session):
    user_id = random.randint(10000, 99999)
    property_id = random.randint(10000, 99999)
    lot_id = random.randint(10000, 99999)
    
    # Real estate registration number aleatorios
    reg_num_property = random.randint(100000, 999999)
    reg_num_lot = random.randint(100000, 999999)
    
    # Document number aleatorio entero de 9 dígitos
    doc_number = random.randint(100000000, 999999999)

    user = User(
        id=user_id,
        name="Juan",
        first_last_name="Perez",
        second_last_name="Lopez",
        document_number=doc_number,
    )
    prop = Property(
        id=property_id,
        name="Finca La Esperanza",
        longitude=1.0,
        latitude=1.0,
        extension=100.0,
        real_estate_registration_number=reg_num_property
    )
    lot = Lot(
        id=lot_id,
        name="Lote 1",
        longitude=1.0,
        latitude=1.0,
        extension=50.0,
        real_estate_registration_number=reg_num_lot,
        payment_interval_id=1,
        state_id=3,
        type_crop_id=1
    )
    dbsession.add_all([user, prop, lot])
    dbsession.commit()

    prop_lot = PropertyLot(property_id=property_id, lot_id=lot_id)
    user_prop = PropertyUser(property_id=property_id, user_id=user_id)
    dbsession.add_all([prop_lot, user_prop])
    dbsession.commit()

    yield user, prop, lot


def test_get_user_info_by_lot(dbsession: Session, setup_data):
    user, prop, lot = setup_data

    service = InvoiceService(dbsession)
    result = service.get_user_info_by_lot(lot.id)

    assert isinstance(result, dict)
    assert result.get("user_id") == user.id
    assert result.get("user_name") == f"{user.name} {user.first_last_name} {user.second_last_name}"
    assert result.get("user_identification") == user.document_number

def test_get_user_info_by_lot_no_result(dbsession: Session):
    service = InvoiceService(dbsession)
    result = service.get_user_info_by_lot(9999999999)
    assert result == {}
