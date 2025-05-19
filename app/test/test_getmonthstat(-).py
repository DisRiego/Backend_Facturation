import random
from datetime import datetime
import pytest
from sqlalchemy.orm import Session
from app.consumption.services import ConsumptionService
from app.facturation.models import (
    PaymentInterval,
    Property,
    Lot,
    PropertyLot,
    Request,
    ConsumptionMeasurement,
)

@pytest.fixture(scope="function")
def db_session():
    # Aquí debes retornar una sesión activa de SQLAlchemy para pruebas
    # Por ejemplo:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def test_get_monthly_stats(db_session: Session):
    # Datos de prueba: año y mes actuales
    today = datetime.utcnow()
    year = today.year
    month = today.month

    # Crear o buscar PaymentInterval
    pi = db_session.query(PaymentInterval).filter_by(name="Mensual").first()
    if not pi:
        pi = PaymentInterval(name="Mensual")
        db_session.add(pi)
        db_session.commit()
        db_session.refresh(pi)

    # Crear o buscar Property con id random
    property_id = random.randint(1000, 9999)
    prop = db_session.query(Property).filter_by(id=property_id).first()
    if not prop:
        prop = Property(
            id=property_id,
            name="Propiedad prueba",
            longitude=0.0,
            latitude=0.0,
            extension=1.0,
            real_estate_registration_number=123456,
            State=3
        )
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

    # Crear o buscar Lot con id random
    lot_id = random.randint(1000, 9999)
    lot = db_session.query(Lot).filter_by(id=lot_id).first()
    if not lot:
        lot = Lot(
            id=lot_id,
            name="Lote prueba",
            longitude=0.0,
            latitude=0.0,
            extension=1.0,
            real_estate_registration_number=654321,
            payment_interval=pi.id,
            State=5
        )
        db_session.add(lot)
        db_session.commit()
        db_session.refresh(lot)

    # Crear relación PropertyLot
    pl = db_session.query(PropertyLot).filter_by(property_id=prop.id, lot_id=lot.id).first()
    if not pl:
        pl = PropertyLot(property_id=prop.id, lot_id=lot.id)
        db_session.add(pl)
        db_session.commit()

    # Crear un Request para el lote
    req = Request(lot_id=lot.id)

    # Asignar atributos para la prueba (evitar error AttributeError)
    req.Temperatura = 25.0
    req.Humedad = 50.0
    req.Altitud = 1500.0
    req.AreaCultivo = 10.0
    req.TipoCultivo = "A"
    req.TipoTierra = "arenosa"

    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)

    # Insertar varias mediciones de consumo para el mes y año indicados
    for day in [5, 15, 25]:
        created_at = datetime(year, month, day, 12, 0, 0)
        consumption = ConsumptionMeasurement(
            request_id=req.id,
            final_volume=100.0 + day,  # volumen variable para diversidad
            created_at=created_at
        )
        db_session.add(consumption)
    db_session.commit()

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
