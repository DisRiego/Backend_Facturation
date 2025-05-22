import pytest
import random
from datetime import datetime, timedelta
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
    PropertyUser,
    User,
)

@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def test_list_all_consumptions(db_session: Session):
    # 1. Crear o reutilizar un usuario
    user = db_session.query(User).filter_by(email="consumption_test@example.com").first()
    if not user:
        user = User(
            name="Test",
            first_last_name="Consumption",
            second_last_name="User",
            email="consumption_test@example.com",
            document_number=str(random.randint(100000000, 999999999)),
            
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    # 2. Crear PaymentInterval
    payment_interval = db_session.query(PaymentInterval).filter_by(name="Mensual").first()
    if not payment_interval:
        payment_interval = PaymentInterval(name="Mensual", interval_days=30)
        db_session.add(payment_interval)
        db_session.commit()
        db_session.refresh(payment_interval)

    # 3. Crear Property
    prop = Property(
        name="Predio Prueba",
        longitude=0.0,
        latitude=0.0,
        extension=1.0,
        real_estate_registration_number=random.randint(100000, 999999),
        State=3
    )
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)

    # 4. Crear Lot
    lot = Lot(
        name="Lote Prueba",
        longitude=0.0,
        latitude=0.0,
        extension=1.0,
        real_estate_registration_number=random.randint(100000, 999999),
        payment_interval_id=payment_interval.id,
        state_id=5
    )
    db_session.add(lot)
    db_session.commit()
    db_session.refresh(lot)

    # 5. Relaciones
    db_session.add(PropertyLot(property_id=prop.id, lot_id=lot.id))
    db_session.add(PropertyUser(property_id=prop.id, user_id=user.id))
    db_session.commit()

    # 6. Crear Request y medición
    request = Request(lot_id=lot.id)
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)

    consumption = ConsumptionMeasurement(
        request_id=request.id,
        final_volume=150.5,
        created_at=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(consumption)
    db_session.commit()

    # 7. Llamar al servicio
    service = ConsumptionService(db_session)
    results = service.list_all_consumptions()

    # Validaciones
    assert isinstance(results, list)
    assert len(results) > 0

    found = any(
        r["lot_id"] == lot.id and
        r["property_id"] == prop.id and
        r["payment_interval"] == "Mensual" and
        abs(r["final_volume"] - 150.5) < 0.001
        for r in results
    )
    assert found, "No se encontró la medición de consumo insertada en los resultados."
