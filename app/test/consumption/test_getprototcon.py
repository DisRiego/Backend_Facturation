import pytest
import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.consumption.services import ConsumptionService
from app.facturation.models import (
    User,
    Property,
    Lot,
    PropertyLot,
    PropertyUser,
    Request,
    ConsumptionMeasurement,
    PaymentInterval,
    TypeCrop,
    Var
)

@pytest.fixture(scope="function")
def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(scope="function")
def test_user_property_setup(db_session: Session):
    # Generar IDs aleatorios para usuario, predio y lote
    user_id = random.randint(10000, 99999)
    property_id = random.randint(10000, 99999)
    lot_id = random.randint(10000, 99999)

    # Generar números de registro únicos
    reg_number_user = str(random.randint(1, 2000000000))  # string para documento usuario
    reg_number_property = random.randint(100000, 999999)
    reg_number_lot = random.randint(100000, 999999)

    # Crear usuario de prueba
    user = User(
        id=user_id,
        name="Usuario Prueba",
        first_last_name="Apellido1",
        second_last_name="Apellido2",
        document_number=reg_number_user
    )
    db_session.add(user)

    # Crear estado (Var) si no existe
    estado_predio = db_session.query(Var).filter_by(id=3).first()
    if not estado_predio:
        estado_predio = Var(id=3, name="Activo")
        db_session.add(estado_predio)

    estado_lote = db_session.query(Var).filter_by(id=5).first()
    if not estado_lote:
        estado_lote = Var(id=5, name="Activo")
        db_session.add(estado_lote)

    # Crear PaymentInterval si no existe
    payment_interval = db_session.query(PaymentInterval).filter_by(name="Mensual").first()
    if not payment_interval:
        payment_interval = PaymentInterval(name="Mensual")
        db_session.add(payment_interval)

    # Crear tipo cultivo si no existe
    type_crop = db_session.query(TypeCrop).first()
    if not type_crop:
        type_crop = TypeCrop(
            id=random.randint(100, 999),
            name="TipoCultivoPrueba",
            harvest_time=30,
            payment_interval_id=payment_interval.id if payment_interval else 1,
            state_id=estado_lote.id if estado_lote else 5
        )
        db_session.add(type_crop)

    db_session.commit()

    # Crear predio
    prop = Property(
        id=property_id,
        name="Predio Test",
        longitude=-74.1,
        latitude=4.6,
        extension=10.0,
        real_estate_registration_number=reg_number_property,
        State=estado_predio.id
    )
    db_session.add(prop)
    db_session.commit()

    # Crear lote
    lot = Lot(
        id=lot_id,
        name="Lote Test",
        longitude=-74.1,
        latitude=4.7,
        extension=5.0,
        real_estate_registration_number=reg_number_lot,
        payment_interval_id=payment_interval.id,
        state_id=estado_lote.id,
        type_crop_id=type_crop.id
    )
    db_session.add(lot)
    db_session.commit()

    # Relacionar predio-lote
    prop_lot = PropertyLot(property_id=prop.id, lot_id=lot.id)
    db_session.add(prop_lot)

    # Relacionar usuario-predio
    user_prop = PropertyUser(property_id=prop.id, user_id=user.id)
    db_session.add(user_prop)

    db_session.commit()

    # Crear request para el lote
    request = Request(lot_id=lot.id)
    db_session.add(request)
    db_session.commit()

    # Crear mediciones para ese request
    for vol in [100.5, 150.75, 120.25]:
        measurement = ConsumptionMeasurement(
            request_id=request.id,
            final_volume=vol,
            created_at=datetime.utcnow()
        )
        db_session.add(measurement)
    db_session.commit()

    yield user.id  # Pasamos el user_id para la prueba

def test_get_properties_total_consumption(db_session: Session, test_user_property_setup):
    user_id = test_user_property_setup

    service = ConsumptionService(db_session)
    response = service.get_properties_total_consumption(user_id)

    assert isinstance(response, dict)
    assert response.get("success") is True
    assert isinstance(response.get("data"), list)
    assert len(response["data"]) > 0

    for item in response["data"]:
        assert "property_id" in item
        assert "property_name" in item
        assert "extension" in item
        assert "measurement_date" in item
        assert "registered_consumption" in item

    # Validar suma correcta de consumo registrado
    total_volumes = 100.5 + 150.75 + 120.25
    found = False
    for item in response["data"]:
        if abs(item["registered_consumption"] - total_volumes) < 0.01:
            found = True
            break
    assert found, "No se encontró el consumo total esperado en la respuesta"
