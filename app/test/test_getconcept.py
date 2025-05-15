import pytest
import random
from decimal import Decimal
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.facturation.services import FacturationService
from app.facturation.schemas import ConceptCreate
from app.facturation.models import Property, Lot, PropertyLot
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
def concept_fixture(dbsession: Session):
    predio_id = random.randint(10000, 99999)
    lote_id = random.randint(10000, 99999)
    reg_number = random.randint(1000000, 9999999)

    predio = Property(
        id=predio_id,
        name="Predio GET",
        longitude=1.0,
        latitude=1.0,
        extension=5.0,
        real_estate_registration_number=reg_number,
        State=3
    )
    lote = Lot(
        id=lote_id,
        name="Lote GET",
        longitude=1.0,
        latitude=1.0,
        extension=3.0,
        real_estate_registration_number=reg_number,
        payment_interval=1,
        State=5
    )
    dbsession.add(predio)
    dbsession.add(lote)
    dbsession.commit()

    relation = PropertyLot(property_id=predio.id, lot_id=lote.id)
    dbsession.add(relation)
    dbsession.commit()

    service = FacturationService(dbsession)
    concept = service.create_concept(ConceptCreate(
        nombre="GET Concept",
        descripcion="Para probar get_concept",
        valor=Decimal("55.55"),
        scope_id=2,
        tipo_id=1,
        predio_id=predio.id,
        lote_id=lote.id
    ))
    return concept.id, predio.name, lote.name

def test_get_concept(dbsession: Session, concept_fixture):
    concept_id, predio_name, lote_name = concept_fixture
    service = FacturationService(dbsession)

    response = service.get_concept(concept_id)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200

    content = json.loads(response.body)
    assert content["success"] is True
    assert content["data"]["nombre"] == "GET Concept"
    assert content["data"]["predio_name"] == predio_name
    assert content["data"]["lote_name"] == lote_name
