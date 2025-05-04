from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from .schemas import (
    BillDetailSchema,
    TransactionSummarySchema,
    TransactionDetailSchema,
    BillsWithStatusCountSchema,
)
from .services import BillingService

router = APIRouter(prefix="/billing", tags=["Billing"])


# Obtener todas las facturas
@router.get("/bills", response_model=BillsWithStatusCountSchema)
def get_all_bills(db: Session = Depends(get_db)):
    service = BillingService(db)
    return service.get_all_bills()


# Ver detalles de una factura
@router.get("/bills/{bill_id}", response_model=BillDetailSchema)
def get_bill_detail(bill_id: int, db: Session = Depends(get_db)):
    service = BillingService(db)
    return service.get_bill_detail(bill_id)


# Obtener facturas por número de documento de usuario
@router.get("/bills/user/{document_number}", response_model=BillsWithStatusCountSchema)
def get_bills_by_user(document_number: str, db: Session = Depends(get_db)):
    service = BillingService(db)
    return service.get_bills_by_user(document_number)


# Obtener todas las transacciones
@router.get("/transactions", response_model=List[TransactionSummarySchema])
def get_all_transactions(db: Session = Depends(get_db)):
    service = BillingService(db)
    return service.get_all_transactions()


# Ver detalles de una transacción
@router.get("/transactions/{transaction_id}", response_model=TransactionDetailSchema)
def get_transaction_detail(transaction_id: int, db: Session = Depends(get_db)):
    service = BillingService(db)
    return service.get_transaction_detail(transaction_id)
