import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.my_facturation.services import MyFacturationService
from app.payu.models import Invoice
from app.facturation.models import User, Lot, PropertyLot, PaymentInterval, Property
from datetime import datetime, timedelta
import random

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(scope="function")
def test_user_with_lots_and_invoices(db_session: Session):
    random_suffix = random.randint(10000, 99999)

    # Crear usuario
    user = User(
        name=f"TestUser{random_suffix}",
        first_last_name="LastName1",
        second_last_name="LastName2",
        document_number=str(random_suffix),
        email=f"user{random_suffix}@test.com"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Usar PaymentInterval existente con id=1 (asegúrate que exista)
    interval = db_session.query(PaymentInterval).filter(PaymentInterval.id == 1).first()
    if not interval:
        raise Exception("No existe PaymentInterval con id=1")

    # Crear propiedad
    prop = Property(
        name=f"TestProperty{random_suffix}",
        longitude=0.0,
        latitude=0.0,
        extension=1.0,
        real_estate_registration_number=random.randint(100000, 999999),
        State=3
    )
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)

    # Crear 2 lotes y asociarlos a la propiedad
    lots = []
    for i in range(2):
        lot = Lot(
            name=f"TestLot{random_suffix}_{i}",
            longitude=0.0,
            latitude=0.0,
            extension=1.0,
            real_estate_registration_number=random.randint(100000, 999999),
            payment_interval=interval,
            state_id=5,
            type_crop_id=1  # Asegúrate que exista tipo cultivo 1 o cambia
        )
        db_session.add(lot)
        db_session.commit()
        db_session.refresh(lot)
        lots.append(lot)

        # Asociar lote con propiedad
        pl = PropertyLot(property_id=prop.id, lot_id=lot.id)
        db_session.add(pl)
        db_session.commit()

    # Crear facturas por lote, varias con fechas distintas
    invoices = []
    for lot in lots:
        for days_ago in [1, 5, 10]:  # Tres facturas por lote, con emisión decreciente
            inv = Invoice(
                reference_code=f"REF{random_suffix}_{lot.id}_{days_ago}",
                client_name=f"Client{random_suffix}",
                client_email=f"client{random_suffix}@email.com",
                issuance_date=datetime.utcnow() - timedelta(days=days_ago),
                expiration_date=datetime.utcnow() + timedelta(days=30),
                invoiced_period=30,
                billing_start_date=datetime.utcnow() - timedelta(days=60),
                billing_end_date=datetime.utcnow() - timedelta(days=30),
                total_amount=100.0 + days_ago,
                lot_id=lot.id,
                user_id=user.id,
                status="pendiente"
            )
            db_session.add(inv)
            db_session.commit()
            db_session.refresh(inv)
            invoices.append(inv)

    yield user, lots, invoices


def test_list_user_latest_invoices_by_lot_success(db_session: Session, test_user_with_lots_and_invoices):
    user, lots, invoices = test_user_with_lots_and_invoices
    service = MyFacturationService(db_session)

    result = service.list_user_latest_invoices_by_lot(user.id)

    assert isinstance(result, list)
    assert len(result) <= 12

    lot_latest_dates = {}
    for row in result:
        lot_id = row["lot_id"]
        iss_date = row["issuance_date"]
        if lot_id not in lot_latest_dates:
            lot_latest_dates[lot_id] = iss_date
        else:
            # Cambiar el sentido de la comparación:
            assert lot_latest_dates[lot_id] >= iss_date

    for lot in lots:
        latest_invoice = max(
            [inv for inv in invoices if inv.lot_id == lot.id],
            key=lambda x: x.issuance_date
        )
        found = any(r["invoice_id"] == latest_invoice.id for r in result)
        assert found


def test_list_user_latest_invoices_by_lot_user_not_found(db_session: Session):
    service = MyFacturationService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        service.list_user_latest_invoices_by_lot(99999999)
    assert exc_info.value.status_code == 404
    assert "Usuario no encontrado" in exc_info.value.detail