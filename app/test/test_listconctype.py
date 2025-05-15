import pytest
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.facturation.services import FacturationService
from app.facturation.models import ConceptType


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


def test_list_concept_types(dbsession: Session):
    service = FacturationService(dbsession)

    results = service.list_concept_types()

    # Validaciones
    assert isinstance(results, list)
    assert all(isinstance(item, ConceptType) for item in results)

    # Validar orden por nombre
    nombres = [ct.name for ct in results]
    assert nombres == sorted(nombres)

