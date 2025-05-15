import pytest
from decimal import Decimal
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.facturation.models import Concept, Property, Lot, PropertyLot
from app.facturation.services import FacturationService


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
def concept_enabled_fixture(dbsession: Session):
    predio = Property(
        name="Predio habilitado",
        longitude=0,
        latitude=0,
        extension=10,
        real_estate_registration_number=1234567,
        State=3
    )
    lote = Lot(
        name="Lote habilitado",
        longitude=0,
        latitude=0,
        extension=5,
        real_estate_registration_number=1234567,
        payment_interval=1,
        State=5
    )
    dbsession.add(predio)
    dbsession.add(lote)
    dbsession.commit()

    relation = PropertyLot(property_id=predio.id, lot_id=lote.id)
    dbsession.add(relation)
    dbsession.commit()

    concept = Concept(
        nombre="Concepto habilitado",
        descripcion="Debe deshabilitarse",
        valor=Decimal("123.45"),
        tipo_id=1,
        scope_id=2,
        predio_id=predio.id,
        lote_id=lote.id,
        estado_id=27  # Activo
    )
    dbsession.add(concept)
    dbsession.commit()
    dbsession.refresh(concept)
    return concept


def test_disable_concept(dbsession: Session, concept_enabled_fixture):
    service = FacturationService(dbsession)
    concept = concept_enabled_fixture
    assert concept.estado_id == 27  # asegurarse que está activo

    response = service.disable_concept(concept.id)
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200

    # Convertimos el contenido en dict para inspección más precisa
    import json
    body = json.loads(response.body.decode())
    assert body["success"] is True
    assert body["data"]["estado_id"] == 28  # validamos el campo correctamente
