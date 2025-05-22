import pytest
import random
import string
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import datetime as dt

from app.main import app
from app.database import SessionLocal
from app.payu.models import Invoice
from app.facturation.models import User, Property, Lot, PropertyLot, PropertyUser

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@pytest.fixture(scope="module")
def sessionlocal():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

import random
import string
import datetime as dt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.facturation.models import User, Property, Lot, PropertyLot, PropertyUser
from app.payu.models import Invoice
from app.main import app

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def random_number_string(length=9):
    return ''.join(random.choices(string.digits, k=length))

@pytest.fixture(scope="function")
def test_user(sessionlocal: Session):
    # Buscar usuario de prueba para evitar duplicados
    user = sessionlocal.query(User).filter(User.email == "testuser@example.com").first()
    if user:
        yield user
        return

    user = User(
        name="Test",
        first_last_name="User",
        second_last_name="Example",
        document_number=random_number_string(9),
        email="testuser@example.com"
    )
    sessionlocal.add(user)
    sessionlocal.commit()
    sessionlocal.refresh(user)
    yield user
    # Limpieza - eliminar usuario solo si fue creado
    try:
        sessionlocal.delete(user)
        sessionlocal.commit()
    except Exception:
        sessionlocal.rollback()

@pytest.fixture(scope="function")
def test_property_and_lot(sessionlocal: Session, test_user: User):
    # Crear propiedad con número de registro inmobiliario aleatorio
    prop = Property(
        name=f"Test Property {random_string(4)}",
        longitude=10.0,
        latitude=10.0,
        extension=100.0,
        real_estate_registration_number=int(random_number_string(6)),
        State=3
    )
    sessionlocal.add(prop)
    sessionlocal.commit()
    sessionlocal.refresh(prop)

    # Crear lote con número de registro inmobiliario aleatorio
    lot = Lot(
        name=f"Test Lot {random_string(4)}",
        longitude=10.0,
        latitude=10.0,
        extension=50.0,
        real_estate_registration_number=int(random_number_string(6)),
        payment_interval_id=1,
        state_id=5,
        type_crop_id=1
    )
    sessionlocal.add(lot)
    sessionlocal.commit()
    sessionlocal.refresh(lot)

    # Relacionar propiedad y lote
    prop_lot = PropertyLot(property_id=prop.id, lot_id=lot.id)
    sessionlocal.add(prop_lot)

    # Relacionar propiedad y usuario
    prop_user = PropertyUser(property_id=prop.id, user_id=test_user.id)
    sessionlocal.add(prop_user)
    sessionlocal.commit()

    yield lot

    # Limpieza
    try:
        sessionlocal.delete(prop_user)
        sessionlocal.delete(prop_lot)
        sessionlocal.delete(lot)
        sessionlocal.delete(prop)
        sessionlocal.commit()
    except Exception:
        sessionlocal.rollback()

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c

def test_create_invoice_success(client: TestClient, sessionlocal: Session, test_property_and_lot: Lot):
    # Limpieza: borrar facturas con reference_code del día para evitar duplicados
    today = dt.datetime.utcnow().strftime('%Y%m%d')
    prefix = f"DISR-{today}-"
    facturas = sessionlocal.query(Invoice).filter(Invoice.reference_code.like(f"{prefix}%")).all()
    for f in facturas:
        sessionlocal.delete(f)
    sessionlocal.commit()

    # Ejecutar el endpoint
    response = client.post("/facturations/create", json={"lot_id": test_property_and_lot.id})

    if response.status_code != 200 and response.status_code != 201:
        print("❌ Respuesta del servidor:", response.text)

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["success"] is True
    assert "data" in data

    invoice = sessionlocal.query(Invoice).filter(Invoice.lot_id == test_property_and_lot.id).order_by(Invoice.id.desc()).first()
    assert invoice is not None
    assert invoice.status == "pendiente"

    # Limpiar factura creada
    sessionlocal.delete(invoice)
    sessionlocal.commit()
