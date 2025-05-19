import pytest
import random
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.consumption.services import ConsumptionService
from app.facturation.models import (
    ConsumptionMeasurement,
    Request,
    Lot,
    PropertyLot,
    PaymentInterval,
    Property,
)
from datetime import datetime, timedelta

@pytest.fixture(scope="function")
def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def test_list_all_consumptions(db_session: Session):
    # Generar IDs aleatorios para property_id y lote_id
    random_property_id = random.randint(1000, 9999)
    random_lot_id = random.randint(1000, 9999)

    # Buscar o crear PaymentInterval "Mensual"
    payment_interval = db_session.query(PaymentInterval).filter_by(name="Mensual").first()
    if not payment_interval:
        payment_interval = PaymentInterval(name="Mensual")
        db_session.add(payment_interval)
        db_session.commit()
        db_session.refresh(payment_interval)

    # Buscar o crear Property con random_property_id
    property_obj = db_session.query(Property).filter_by(id=random_property_id).first()
    if not property_obj:
        property_obj = Property(
            id=random_property_id,
            name="Predio prueba",
            longitude=0.0,
            latitude=0.0,
            extension=1.0,
            real_estate_registration_number=123456,
            State=3
        )
        db_session.add(property_obj)
        db_session.commit()
        db_session.refresh(property_obj)

    # Crear Lot con id aleatorio
    lot = db_session.query(Lot).filter_by(id=random_lot_id).first()
    if not lot:
        lot = Lot(
            id=random_lot_id,
            name="Lote prueba",
            longitude=0.0,
            latitude=0.0,
            extension=1.0,
            real_estate_registration_number=654321,
            payment_interval=payment_interval.id,
            State=5
        )
        db_session.add(lot)
        db_session.commit()
        db_session.refresh(lot)

    # Crear relación PropertyLot (predio-lote)
    pl = db_session.query(PropertyLot).filter_by(property_id=property_obj.id, lot_id=lot.id).first()
    if not pl:
        pl = PropertyLot(property_id=property_obj.id, lot_id=lot.id)
        db_session.add(pl)
        db_session.commit()

    # Crear Request para el lote
    request = Request(lot_id=lot.id)
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)

    # Crear medición de consumo
    consumption = ConsumptionMeasurement(
        request_id=request.id,
        final_volume=150.5,
        created_at=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(consumption)
    db_session.commit()
    db_session.refresh(consumption)

    service = ConsumptionService(db_session)
    results = service.list_all_consumptions()

    assert isinstance(results, list)
    assert len(results) > 0

    found = False
    for r in results:
        if (
            r["lot_id"] == lot.id and
            r["property_id"] == property_obj.id and
            r["payment_interval"] == "Mensual" and
            abs(r["final_volume"] - 150.5) < 0.001
        ):
            found = True
            break

    assert found, "No se encontró la medición de consumo insertada en los resultados."
