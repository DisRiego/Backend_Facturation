import pytest
from app.factus.services import FactusService
from app.payu.models import Payment, Invoice
from app.database import SessionLocal
from app.facturation.services import InvoiceService

@pytest.fixture(scope="module")
def sessionlocal():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_obtener_token_factus(sessionlocal):
    service = FactusService(sessionlocal)
    token = service.obtener_token_factus()
    assert isinstance(token, str)
    assert len(token) > 0

def test_get_concepts_invoice(sessionlocal):
    service = FactusService(sessionlocal)
    # Cambia por un invoice_id válido en tu BD
    invoice_id = sessionlocal.query(Invoice.id).first()[0]
    concepts = service.get_concepts_invoice(invoice_id)
    assert isinstance(concepts, list)
    for concept in concepts:
        assert "code_reference" in concept
        assert "concept_name" in concept
        assert "quantity" in concept
        assert "price" in concept

def test_generate_and_download_invoice(sessionlocal):
    factus_service = FactusService(sessionlocal)
    invoice_service = InvoiceService(sessionlocal)

    # Obtener un pago con invoice_id
    payment = sessionlocal.query(Payment).filter(Payment.invoice_id != None).first()
    assert payment is not None, "No hay pagos con factura en la base de datos"

    # Obtener la factura relacionada
    invoice = sessionlocal.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
    assert invoice is not None, "No se encontró la factura asociada al pago"

    # Obtener información del usuario desde InvoiceService
    user_info = invoice_service.get_user_info_by_lot(invoice.lot_id)
    assert user_info != {}, "No se encontró info de usuario para el lote"

    # Generar factura en Factus, debe crear y asignar factus_number
    result_generate = factus_service.generate_invoice_from_payment(payment, user_info)
    assert result_generate["success"] is True, f"Error generando factura: {result_generate.get('error')}"

    # Refrescar para obtener factus_number actualizado en DB
    sessionlocal.refresh(invoice)
    assert invoice.factus_number is not None, "factus_number no fue asignado"

    # Descargar PDF y XML usando el número generado
    result_download = factus_service.descargar_pdf_xml_factura(invoice.id)
    assert result_download.get("success") is True, f"Error descargando documentos: {result_download.get('error')}"
    assert "pdf_url" in result_download, "No se devolvió pdf_url"
    assert "xml_url" in result_download, "No se devolvió xml_url"

    print("Prueba completa de generación y descarga de factura exitosa.")
