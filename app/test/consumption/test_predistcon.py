import random
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.database import SessionLocal
from app.facturation.models import TypeCrop, Lot
from app.main import app
from app.consumption.services import ConsumptionService

@pytest.fixture(scope="function")
def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(scope="function")
def client(db_session: Session):
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def setup_minimal_data(db_session: Session):
    # Elegir un TypeCrop existente cualquiera
    type_crop = db_session.query(TypeCrop).first()
    assert type_crop is not None, "No hay TypeCrop en la base de datos."

    # Crear un lote mínimo para test con el TypeCrop existente
    lot_id = random.randint(10000, 99999)
    lot = Lot(
        id=lot_id,
        name="Lote Test",
        longitude=1.0,
        latitude=1.0,
        extension=10.0,
        real_estate_registration_number=random.randint(100000, 999999),
        payment_interval_id=1,  # Mensual ya existe con id 1
        state_id=5,             # Estado 'Activo' con id 5 ya existe
        type_crop_id=type_crop.id,
    )
    db_session.add(lot)
    db_session.commit()

    return {
        "lot": lot,
        "type_crop": type_crop,
    }

def test_predict_district_consumption(db_session: Session, setup_minimal_data):
    service = ConsumptionService(db_session)

    result = service.predict_district_consumption()

    assert "success" in result
    assert result["success"] is True
    assert "data" in result
    assert "details" in result["data"]
    assert isinstance(result["data"]["details"], list)
    assert "total_predicted_consumption" in result["data"]
    assert isinstance(result["data"]["total_predicted_consumption"], float)

    # Verificar que el lote creado esté en el detalle
    assert any(d["lot_id"] == setup_minimal_data["lot"].id for d in result["data"]["details"])
