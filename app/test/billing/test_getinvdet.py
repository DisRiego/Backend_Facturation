import pytest
from app.billing.services import BillingService
from app.database import SessionLocal
from datetime import datetime

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_list_invoices_general(db_session):
    service = BillingService(db_session)
    result = service.list_invoices_general()

    assert isinstance(result, list)

    if len(result) > 0:
        expected_keys = {
            "invoice_id",
            "invoice_number",
            "property_id",
            "lot_id",
            "client_document",
            "payment_interval",
            "issuance_date",
            "expiration_date",
            "amount_due",
            "invoice_status",
            "dian_status",
        }
        for invoice in result:
            assert isinstance(invoice, dict)
            assert expected_keys.issubset(invoice.keys())

            assert isinstance(invoice["invoice_id"], int)
            assert isinstance(invoice["invoice_number"], (str, type(None)))
            assert isinstance(invoice["property_id"], (int, type(None)))
            assert isinstance(invoice["lot_id"], (int, type(None)))
            # Aceptar también int aquí
            assert isinstance(invoice["client_document"], (str, int, type(None)))
            assert isinstance(invoice["payment_interval"], (str, type(None)))
            assert isinstance(invoice["issuance_date"], datetime)
            assert isinstance(invoice["expiration_date"], datetime)
            assert isinstance(invoice["amount_due"], (float, int))
            assert isinstance(invoice["invoice_status"], (str, type(None)))
            assert isinstance(invoice["dian_status"], (str, type(None)))
            break
