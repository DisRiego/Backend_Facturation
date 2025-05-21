import pytest
import random
from decimal import Decimal
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.facturation.models import Concept, Property, Lot, PropertyLot
from app.facturation.services import FacturationService
import json

@pytest.fixture(scope="module")
def sessionlocal():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def dbsession(sessionlocal):
    yield sessionlocal

@pytest.fixture(scope="function")
def concept_disabled_fixture(dbsession: Session):
    predio_id = random.randint(10000, 99999)
    lote_id = random.randint(10000, 99999)
    reg_number = random.randint(1000000, 9999999)

    predio = Property(
        id=predio_id,
        name="Predio habilitar",
        longitude=1.0,
        latitude=1.0,
        extension=10.0,
        real_estate_registration_number=reg_number,
        State=3
    )
    lote = Lot(
        id=lote_id,
        name="Lote habilitar",
        longitude=1.0,
        latitude=1.0,
        extension=5.0,
        real_estate_registration_number=reg_number,
        payment_interval_id=1,
        state_id=5
    )
    dbsession.add_all([predio, lote])
    dbsession.commit()

    dbsession.add(PropertyLot(property_id=predio_id, lot_id=lote_id))
    dbsession.commit()

    concept = Concept(
        nombre="Concepto deshabilitado",
        descripcion="Debe habilitarse",
        valor=Decimal("123.45"),
        scope_id=2,
        tipo_id=1,
        estado_id=28,  # Deshabilitado
        predio_id=predio_id,
        lote_id=lote_id
    )
    dbsession.add(concept)
    dbsession.commit()
    dbsession.refresh(concept)
    return concept

def test_enable_concept(dbsession: Session, concept_disabled_fixture):
    service = FacturationService(dbsession)
    concept = concept_disabled_fixture
    assert concept.estado_id == 28  # asegurarse que está deshabilitado

    response = service.enable_concept(concept.id)
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200

    content = json.loads(response.body.decode())
    assert content["success"] is True
    assert content["data"]["estado_id"] == 27

def test_enable_concept_not_found(dbsession: Session):
    service = FacturationService(dbsession)
    response = service.enable_concept(9999999)
    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert "Concepto no encontrado" in response.body.decode()
