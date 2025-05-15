import pytest
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.facturation.services import FacturationService
from app.facturation.models import ScopeType


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


def test_list_scope_types(dbsession: Session):
    service = FacturationService(dbsession)

    results = service.list_scope_types()

    # Validaciones
    assert isinstance(results, list)
    assert all(isinstance(item, ScopeType) for item in results)

    # Validar que estén ordenados por nombre
    nombres = [s.name for s in results]
    assert nombres == sorted(nombres)
    
    # Validar que contiene los elementos esperados
    nombres_esperados = {"General", "Específico"}
    assert nombres_esperados.issubset(set(nombres))
