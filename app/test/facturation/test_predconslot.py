import pytest
from fastapi import HTTPException
from app.facturation.services import FacturationService
from app.facturation.models import Lot
from app.database import SessionLocal
from fastapi.testclient import TestClient
from app.main import app

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

@pytest.fixture(scope="function")
def setup_lot(db_session):
    # Confirmar que lote con ID 1 existe y tiene type_crop_id válido
    lote = db_session.get(Lot, 1)
    if not lote:
        pytest.skip("No existe lote con ID 1 en la base de datos para pruebas")
    return lote

def test_predict_consumption_by_lot(db_session, setup_lot):
    service = FacturationService(db_session)

    # Lote válido (id=1)
    result = service.predict_consumption_by_lot(1)

    # Validar la estructura del resultado
    assert isinstance(result, dict)
    assert "prediccion_consumo_base" in result
    assert "promedio_historico_consumo" in result
    assert "prediccion_lluvia_mm" in result
    assert "factor_ajuste_por_clase" in result
    assert "consumo_ajustado_final" in result

def test_predict_consumption_by_lot_lot_no_exist(db_session):
    service = FacturationService(db_session)
    lote_inexistente_id = 999999  # Un id que seguramente no exista

    with pytest.raises(HTTPException) as exc_info:
        service.predict_consumption_by_lot(lote_inexistente_id)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Lote no encontrado"
