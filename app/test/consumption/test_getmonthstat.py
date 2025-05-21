import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.facturation.models import Property, Lot, PropertyLot, Request, ConsumptionMeasurement
from app.consumption.services import ConsumptionService

@pytest.fixture(scope="function")
def db_session():
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def test_get_monthly_stats_existing_data(db_session: Session):
    
    property_id = 8
    lot_id = 1
    request_id = 3  

    
    year = 2025
    month = 4

    # Buscar predio y lote, fallar si no existen
    prop = db_session.query(Property).filter_by(id=property_id).first()
    assert prop is not None, "No existe el predio con id=8 en la base de datos"

    lot = db_session.query(Lot).filter_by(id=lot_id).first()
    assert lot is not None, "No existe el lote con id=1 en la base de datos"

    # Verificar que el lote esté relacionado con el predio
    pl = db_session.query(PropertyLot).filter_by(property_id=prop.id, lot_id=lot.id).first()
    assert pl is not None, f"El lote {lot_id} no está relacionado con el predio {property_id}"

    # Buscar request por id fijo
    req = db_session.query(Request).filter_by(id=request_id).first()
    assert req is not None, f"No existe la solicitud (request) con id {request_id}"

    # Buscar al menos una medición para ese request en el mes/año indicados usando func.extract
    consumption = (
        db_session.query(ConsumptionMeasurement)
        .filter(
            ConsumptionMeasurement.request_id == req.id,
            func.extract('year', ConsumptionMeasurement.created_at) == year,
            func.extract('month', ConsumptionMeasurement.created_at) == month,
        )
        .first()
    )
    assert consumption is not None, f"No hay consumos registrados para el mes {month} y año {year} para la solicitud {req.id}"

    # Crear instancia del servicio
    service = ConsumptionService(db_session)

    # Ejecutar método bajo prueba
    stats = service.get_monthly_stats(year, month)

    # Validar que el resultado contenga las claves esperadas
    assert "registered_avg" in stats
    assert "projected_avg" in stats
    assert "variation_percent" in stats

    # Validar que los valores sean numéricos y plausibles
    assert isinstance(stats["registered_avg"], float)
    assert isinstance(stats["projected_avg"], float)
    assert isinstance(stats["variation_percent"], float)
