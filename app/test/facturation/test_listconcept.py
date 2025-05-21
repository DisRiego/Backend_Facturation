import pytest
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.facturation.services import FacturationService
from app.facturation.models import Concept, Property, Lot, PropertyLot
from app.database import SessionLocal
import random
from decimal import Decimal

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
def setup_concept_with_relations(dbsession: Session):
    # Crear predio y lote
    predio_id = random.randint(10000, 99999)
    lote_id = random.randint(10000, 99999)
    real_estate_reg_num = random.randint(1000000, 9999999)

    predio = Property(
        id=predio_id,
        name="Predio para listar",
        longitude=0,
        latitude=0,
        extension=100,
        real_estate_registration_number=real_estate_reg_num,
        State=3
    )
    lote = Lot(
        id=lote_id,
        name="Lote para listar",
        longitude=0,
        latitude=0,
        extension=50,
        real_estate_registration_number=real_estate_reg_num,
        payment_interval_id=1,
        state_id=5
    )
    dbsession.add(predio)
    dbsession.add(lote)
    dbsession.commit()

    # Relación predio-lote
    relation = PropertyLot(property_id=predio.id, lot_id=lote.id)
    dbsession.add(relation)
    dbsession.commit()

    # Crear concepto asociado
    concept = Concept(
        nombre="Concepto para listar",
        descripcion="Concepto de prueba para listar conceptos",
        valor=Decimal("123.45"),
        scope_id=2,
        tipo_id=1,
        predio_id=predio.id,
        lote_id=lote.id,
        estado_id=27
    )
    dbsession.add(concept)
    dbsession.commit()
    dbsession.refresh(concept)

    yield dbsession, concept, predio, lote


def test_list_concepts(dbsession: Session, setup_concept_with_relations):
    dbsession, concept, predio, lote = setup_concept_with_relations
    service = FacturationService(dbsession)

    response = service.list_concepts()
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200

    data = response.body.decode()
    assert concept.nombre in data
    assert predio.name in data
    assert lote.name in data
    assert concept.descripcion in data