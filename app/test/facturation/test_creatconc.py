import pytest
import random
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.facturation.services import FacturationService
from app.facturation.schemas import ConceptCreate
from app.facturation.models import Property, Lot, PropertyLot

@pytest.fixture(scope="module")
def sessionlocal():
    # Solo abrir y cerrar sesión sin tocar esquema ni limpiar
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def dbsession(sessionlocal):
    db = sessionlocal
    yield db
    # No hacemos rollback ni limpieza para preservar datos

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def setup_property_and_lot(dbsession: Session):
    predio_id = random.randint(10000, 99999)
    lote_id = random.randint(10000, 99999)
    registration_number = random.randint(1000000, 9999999)

    prop = Property(
        id=predio_id,
        name="Test Property",
        longitude=1.0,
        latitude=1.0,
        extension=10.0,
        real_estate_registration_number=registration_number,
        State=3
    )
    lot = Lot(
        id=lote_id,
        name="Test Lot",
        longitude=1.0,
        latitude=1.0,
        extension=5.0,
        real_estate_registration_number=registration_number,
        payment_interval_id=1,
        state_id=5
    )
    dbsession.add(prop)
    dbsession.add(lot)
    dbsession.commit()

    # Agregar relación entre predio y lote para que pase la validación
    relation = PropertyLot(property_id=prop.id, lot_id=lot.id)
    dbsession.add(relation)
    dbsession.commit()

    yield prop, lot

    # No hacemos limpieza para que queden persistidos


def test_create_concept_general_scope(dbsession: Session):
    service = FacturationService(dbsession)
    payload = ConceptCreate(
        nombre="Concepto General Test",
        descripcion="Test creación concepto general",
        valor=10.0,
        scope_id=1,
        tipo_id=1
    )
    concept = service.create_concept(payload)
    assert concept.id is not None
    assert concept.scope_id == 1
    assert concept.predio_id is None
    assert concept.lote_id is None

def test_create_concept_specific_scope(dbsession: Session, setup_property_and_lot):
    service = FacturationService(dbsession)
    prop, lot = setup_property_and_lot

    payload = ConceptCreate(
        nombre="Concepto Específico Test",
        descripcion="Test creación concepto específico",
        valor=15.5,
        scope_id=2,
        tipo_id=3,
        predio_id=prop.id,
        lote_id=lot.id
    )
    concept = service.create_concept(payload)
    assert concept.id is not None
    assert concept.scope_id == 2
    assert concept.predio_id == prop.id
    assert concept.lote_id == lot.id

def test_create_concept_invalid_general_scope_with_predio_lote(dbsession: Session, setup_property_and_lot):
    service = FacturationService(dbsession)
    prop, lot = setup_property_and_lot

    payload = ConceptCreate(
        nombre="Concepto inválido General",
        descripcion="No debe permitir predio/lote en general",
        valor=5.0,
        scope_id=1,
        tipo_id=2,
        predio_id=prop.id,
        lote_id=lot.id
    )

    import pytest
    with pytest.raises(Exception) as excinfo:
        service.create_concept(payload)
    assert excinfo.value.status_code == 400

def test_create_concept_invalid_specific_scope_missing_predio_or_lote(dbsession: Session):
    service = FacturationService(dbsession)

    payload_missing_predio = ConceptCreate(
        nombre="Inválido sin predio",
        descripcion="Falta predio",
        valor=20.0,
        scope_id=2,
        tipo_id=4,
        lote_id=1234
    )
    import pytest
    with pytest.raises(Exception) as excinfo:
        service.create_concept(payload_missing_predio)
    assert excinfo.value.status_code == 400

    payload_missing_lote = ConceptCreate(
        nombre="Inválido sin lote",
        descripcion="Falta lote",
        valor=20.0,
        scope_id=2,
        tipo_id=4,
        predio_id=5678
    )
    with pytest.raises(Exception) as excinfo:
        service.create_concept(payload_missing_lote)
    assert excinfo.value.status_code == 400
