import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.my_facturation.services import MyFacturationService
from app.payu.models import Invoice
from app.facturation.models import User, Lot

@pytest.fixture(scope="function")
def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        # No hacemos rollback ni borrado para preservar datos
        db.close()

@pytest.fixture
def test_user(db_session: Session) -> User:
    user = db_session.query(User).filter_by(document_number="1234567890").first()
    if not user:
        user = User(
            name="Usuario",
            first_last_name="De",
            second_last_name="Prueba",
            document_number="1234567890"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def test_invoices(db_session: Session, test_user: User):
    # Obtener un lote existente (lote)
    lote = db_session.query(Lot).first()
    if lote is None:
        raise Exception("No hay registros en la tabla Lot. Debes tener al menos uno para esta prueba.")

    ref_codes = {"REF-PAID-001", "REF-PEND-001", "REF-OVERDUE-001"}
    existing_invoices = db_session.query(Invoice).filter(Invoice.reference_code.in_(ref_codes)).all()
    existing_refs = {inv.reference_code for inv in existing_invoices}

    invoices_to_create = []

    today = datetime.utcnow()
    past_date = today - timedelta(days=40)
    future_date = today + timedelta(days=40)

    if "REF-PAID-001" not in existing_refs:
        invoices_to_create.append(
            Invoice(
                reference_code="REF-PAID-001",
                client_name="Cliente Pagado",
                client_email="paid@example.com",
                issuance_date=past_date,
                expiration_date=past_date + timedelta(days=15),
                invoiced_period="30",
                billing_start_date=past_date,
                billing_end_date=past_date + timedelta(days=30),
                total_amount=100.0,
                lot_id=lote.id,        # Aquí asignas el id válido
                user_id=test_user.id,
                status="pagada",
                pdf_url=None,
                xml_url=None
            )
        )
    # Repite lo mismo para las otras facturas:
    if "REF-PEND-001" not in existing_refs:
        invoices_to_create.append(
            Invoice(
                reference_code="REF-PEND-001",
                client_name="Cliente Pendiente",
                client_email="pending@example.com",
                issuance_date=past_date,
                expiration_date=future_date,
                invoiced_period="30",
                billing_start_date=past_date,
                billing_end_date=past_date + timedelta(days=30),
                total_amount=200.0,
                lot_id=lote.id,
                user_id=test_user.id,
                status="pendiente",
                pdf_url=None,
                xml_url=None
            )
        )
    if "REF-OVERDUE-001" not in existing_refs:
        invoices_to_create.append(
            Invoice(
                reference_code="REF-OVERDUE-001",
                client_name="Cliente Vencido",
                client_email="overdue@example.com",
                issuance_date=past_date,
                expiration_date=past_date - timedelta(days=5),
                invoiced_period="30",
                billing_start_date=past_date - timedelta(days=35),
                billing_end_date=past_date - timedelta(days=5),
                total_amount=150.0,
                lot_id=lote.id,
                user_id=test_user.id,
                status="pendiente",
                pdf_url=None,
                xml_url=None
            )
        )

    if invoices_to_create:
        db_session.add_all(invoices_to_create)
        db_session.commit()
        for inv in invoices_to_create:
            db_session.refresh(inv)

    all_invoices = db_session.query(Invoice).filter(Invoice.reference_code.in_(ref_codes)).all()
    return all_invoices


def test_get_user_invoice_summary_success(db_session: Session, test_user: User, test_invoices):
    service = MyFacturationService(db_session)
    summary = service.get_user_invoice_summary(test_user.id)

    assert isinstance(summary, dict)
    assert "total" in summary
    assert "paid" in summary
    assert "pending" in summary
    assert "overdue" in summary

    # Chequeamos los conteos; si las facturas ya existían, pueden ser iguales o mayores
    assert summary["total"] >= 3
    assert summary["paid"] >= 1
    assert summary["pending"] >= 2
    assert summary["overdue"] >= 1

def test_get_user_invoice_summary_user_not_found(db_session: Session):
    service = MyFacturationService(db_session)
    non_existent_user_id = 9999999

    with pytest.raises(HTTPException) as exc:
        service.get_user_invoice_summary(non_existent_user_id)
    assert exc.value.status_code == 404
    assert exc.value.detail == "Usuario no encontrado"
