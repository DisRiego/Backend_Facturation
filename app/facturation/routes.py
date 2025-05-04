from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database import get_db
from app.facturation.services import FacturationService
from app.facturation.services import NotificationService
from app.facturation.schemas import NotificationResponse, NotificationList, MarkNotificationRead

router = APIRouter(prefix="/facturation", tags=["Facturation"])

@router.get("/", response_model=Dict)
def get_facturation(db: Session = Depends(get_db)):
    """Obtener todos los mantenimientos"""
    facturation_service = FacturationService(db)
    return facturation_service.get_facturation()

# ===============================
# Endpoints de Notificaciones
# ===============================

@router.get("/notifications/user/{user_id}")
def get_user_notifications(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtener notificaciones de un usuario"""
    facturation_service = FacturationService(db)
    return facturation_service.get_user_notifications(user_id, skip, limit)

@router.put("/notifications/read/{notification_id}")
def mark_notification_as_read(
    notification_id: int,
    user_id: int = Query(..., description="ID del usuario"),
    db: Session = Depends(get_db)
):
    """Marcar una notificación como leída"""
    facturation_service = FacturationService(db)
    return facturation_service.mark_notification_as_read(notification_id, user_id)

# ===============================
# Endpoints de Prueba para Notificaciones
# ===============================

@router.post("/test/invoice")
def test_create_invoice(
    invoice_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Endpoint de prueba para crear factura con notificación"""
    facturation_service = FacturationService(db)
    return facturation_service.create_invoice(invoice_data)

@router.post("/test/payment/{invoice_id}")
def test_process_payment(
    invoice_id: int,
    payment_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Endpoint de prueba para procesar pago con notificación"""
    facturation_service = FacturationService(db)
    return facturation_service.process_payment(invoice_id, payment_data)

@router.put("/test/concept/{concept_id}")
def test_update_concept(
    concept_id: int,
    concept_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Endpoint de prueba para actualizar concepto con notificación"""
    facturation_service = FacturationService(db)
    return facturation_service.update_concept(concept_id, concept_data)

@router.post("/test/transaction/{transaction_id}")
def test_process_transaction(
    transaction_id: int,
    status: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Endpoint de prueba para procesar transacción con notificación"""
    facturation_service = FacturationService(db)
    return facturation_service.process_transaction(transaction_id, status)
