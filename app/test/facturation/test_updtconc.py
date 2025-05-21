import pytest
import random
from decimal import Decimal
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.facturation.services import FacturationService
from app.facturation.schemas import ConceptUpdate
from app.facturation.models import Concept, Property, Lot, PropertyLot


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
def setup_concept_and_related(dbsession: Session):
    predio_id = random.randint(10000, 99999)
    lote_id = random.randint(10000, 99999)
    registration_number = random.randint(1000000, 9999999)

    predio = Property(
        id=predio_id,
        name="Predio para update",
        longitude=0,
        latitude=0,
        extension=100,
        real_estate_registration_number=registration_number,
        State=3
    )
    lote = Lot(
        id=lote_id,
        name="Lote para update",
        longitude=0,
        latitude=0,
        extension=50,
        real_estate_registration_number=registration_number,
        payment_interval_id=1,
        state_id=5
    )

    dbsession.add(predio)
    dbsession.add(lote)
    dbsession.commit()

    # Establecer relación entre predio y lote
    dbsession.add(PropertyLot(property_id=predio.id, lot_id=lote.id))
    dbsession.commit()

    concept = Concept(
        nombre="Concepto Inicial",
        descripcion="Descripción inicial",
        valor=Decimal("100.00"),
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


def test_update_concept_valid_specific_scope(dbsession: Session, setup_concept_and_related):
    dbsession, concept, predio, lote = setup_concept_and_related
    service = FacturationService(dbsession)

    update_payload = ConceptUpdate(
        nombre="Concepto Actualizado",
        descripcion="Descripción actualizada",
        valor=Decimal("150.00"),
        scope_id=2,
        tipo_id=2,
        predio_id=predio.id,
        lote_id=lote.id
    )

    response = service.update_concept(concept.id, update_payload)
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    body = response.body.decode()
    assert "Concepto Actualizado" in body
    assert "Descripción actualizada" in body


def test_update_concept_change_to_general_with_predio_lote(dbsession: Session, setup_concept_and_related):
    dbsession, concept, predio, lote = setup_concept_and_related
    service = FacturationService(dbsession)

    update_payload = ConceptUpdate(
        nombre=concept.nombre,
        descripcion=concept.descripcion,
        valor=concept.valor,
        scope_id=1,
        tipo_id=concept.tipo_id,
        predio_id=predio.id,
        lote_id=lote.id
    )

    response = service.update_concept(concept.id, update_payload)
    assert response.status_code == 400
    assert "No puede especificar predio_id ni lote_id" in response.body.decode()


def test_update_concept_invalid_missing_predio_or_lote(dbsession: Session, setup_concept_and_related):
    dbsession, concept, predio, lote = setup_concept_and_related
    service = FacturationService(dbsession)

    response = service.update_concept(concept.id, ConceptUpdate(
        nombre=concept.nombre,
        descripcion=concept.descripcion,
        valor=concept.valor,
        scope_id=2,
        tipo_id=concept.tipo_id,
        predio_id=None,
        lote_id=lote.id
    ))
    assert response.status_code == 400
    assert "predio_id y lote_id son obligatorios" in response.body.decode()

    response = service.update_concept(concept.id, ConceptUpdate(
        nombre=concept.nombre,
        descripcion=concept.descripcion,
        valor=concept.valor,
        scope_id=2,
        tipo_id=concept.tipo_id,
        predio_id=predio.id,
        lote_id=None
    ))
    assert response.status_code == 400
    assert "predio_id y lote_id son obligatorios" in response.body.decode()


def test_update_concept_lote_not_belong_to_predio(dbsession: Session, setup_concept_and_related):
    dbsession, concept, predio, _ = setup_concept_and_related
    service = FacturationService(dbsession)

    # Crear un lote sin relación con el predio
    lote_id_no_relacionado = random.randint(100000, 999999)
    nuevo_lote = Lot(
        id=lote_id_no_relacionado,
        name="Lote sin relación",
        longitude=0,
        latitude=0,
        extension=20,
        real_estate_registration_number=1112223,
        payment_interval_id=1,
        state_id=5
    )
    dbsession.add(nuevo_lote)
    dbsession.commit()

    update_payload = ConceptUpdate(
        nombre=concept.nombre,
        descripcion=concept.descripcion,
        valor=concept.valor,
        scope_id=2,
        tipo_id=concept.tipo_id,
        predio_id=predio.id,
        lote_id=lote_id_no_relacionado
    )

    response = service.update_concept(concept.id, update_payload)
    assert response.status_code == 400
    assert "no pertenece al predio" in response.body.decode()


def test_update_concept_not_found(dbsession: Session):
    service = FacturationService(dbsession)

    update_payload = ConceptUpdate(
        nombre="No existe",
        descripcion="Intento actualizar concepto inexistente",
        valor=Decimal("100.00"),
        scope_id=1,
        tipo_id=1,
        predio_id=None,
        lote_id=None
    )

    response = service.update_concept(9999999, update_payload)
    assert response.status_code == 404
    assert "Concepto no encontrado" in response.body.decode()
