import pytest
from fastapi.testclient import TestClient
from app.main import app  # Importa tu instancia de FastAPI
from app.database import SessionLocal
from app.facturation.models import Lot, TypeCrop
from sqlalchemy.orm import Session

@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(scope="function")
def client():
    return TestClient(app)

def test_predict_consumption_existing_lot(db_session: Session, client: TestClient):
    # Verificar que el lote con id=1 existe y tiene type_crop_id=1
    lot = db_session.query(Lot).filter_by(id=1).first()
    assert lot is not None, "El lote con id=1 no existe en la base de datos"
    assert lot.type_crop_id == 1, "El lote con id=1 no tiene type_crop_id=1"

    # Construir el payload para la petición POST
    payload = {"lot_id": lot.id}

    # Hacer la petición al endpoint que usa MLService.predict_consumption
    response = client.post("/facturations/predict-consumption", json=payload)

    # Verificar que la petición fue exitosa
    assert response.status_code == 200

    data = response.json()

    # Validar que la respuesta tenga los campos esperados
    assert "prediccion_consumo_base" in data
    assert "promedio_historico_consumo" in data
    assert "prediccion_lluvia_mm" in data
    assert "factor_ajuste_por_clase" in data
    assert "consumo_ajustado_final" in data

    # Validar tipos de datos de la respuesta
    assert isinstance(data["prediccion_consumo_base"], float)
    assert isinstance(data["promedio_historico_consumo"], (float, type(None)))
    assert isinstance(data["prediccion_lluvia_mm"], float)
    assert isinstance(data["factor_ajuste_por_clase"], (float, int))
    assert isinstance(data["consumo_ajustado_final"], float)
