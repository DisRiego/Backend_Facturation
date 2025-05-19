# app/test/test_getconsumdet.py

import pytest
import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.facturation.models import (
    Property, Lot, PropertyLot, Request, ConsumptionMeasurement
)
from app.consumption.services import ConsumptionService
from app.facturation.schemas import PredictInput


@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def test_get_consumption_detail(db_session: Session):
    # IDs aleatorios y matrículas únicas
    property_id = random.randint(1000, 9999)
    lot_id = random.randint(1000, 9999)
    reg_number_property = random.randint(100000, 999999)
    reg_number_lot = random.randint(100000, 999999)

    # Crear Property
    prop = Property(
        id=property_id,
        name="Predio de prueba",
        longitude=1.23,
        latitude=4.56,
        extension=10.0,
        real_estate_registration_number=reg_number_property,
        State=3
    )
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)

    # Crear Lot
    lot = Lot(
        id=lot_id,
        name="Lote de prueba",
        longitude=1.11,
        latitude=2.22,
        extension=5.0,
        real_estate_registration_number=reg_number_lot,
        payment_interval=1,
        State=5
    )
    db_session.add(lot)
    db_session.commit()
    db_session.refresh(lot)

    # Relacionar Property y Lot
    prop_lot = PropertyLot(property_id=prop.id, lot_id=lot.id)
    db_session.add(prop_lot)
    db_session.commit()

    # Crear Request asociado al lote
    request = Request(lot_id=lot.id)
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)

    # Crear varias mediciones de consumo para ese request
    measurements = []
    for vol, day in zip([100.0, 120.0, 110.0], [5, 10, 15]):
        m = ConsumptionMeasurement(
            request_id=request.id,
            final_volume=vol,
            created_at=datetime(datetime.utcnow().year, datetime.utcnow().month, day)
        )
        db_session.add(m)
        db_session.commit()
        db_session.refresh(m)
        measurements.append(m)

    # Instanciar el servicio
    service = ConsumptionService(db_session)

    # Llamar el método bajo prueba usando el ID de la primera medición
    result = service.get_consumption_detail(measurements[0].id)

    # Verificar la estructura esperada
    assert result["measurement_id"] == measurements[0].id
    assert result["property_id"] == prop.id
    assert result["lot_id"] == lot.id
    assert result["property_name"] == prop.name
    assert result["lot_name"] == lot.name
    assert "registered_avg" in result
    assert "projected_avg" in result
    assert "variation_percent" in result
    assert isinstance(result["records"], list)
    assert len(result["records"]) == 3  # Se insertaron 3 mediciones
