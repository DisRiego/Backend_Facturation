from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List
from .models import Bill, BillConcept, Transaction, User
from .schemas import (
    BillSummarySchema,
    BillDetailSchema,
    TransactionSummarySchema,
    TransactionDetailSchema,
    ConceptSchema,
)

class BillingService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_bills(self):
        bills = self.db.query(Bill).all()

        summary = [
            BillSummarySchema(
                bill_number=b.bill_number,
                property_id=b.property_id,
                lot_id=b.lot_id,
                user_document=b.user.document_number,
                payment_interval=b.payment_interval,
                emission_date=b.emission_date,
                due_date=b.due_date,
                amount_due=b.amount_due,
                status=b.status,
            )
            for b in bills
        ]

        # Conteo por estado
        status_counts = {}
        for b in bills:
            status_counts[b.status] = status_counts.get(b.status, 0) + 1

        return {
            "facturas": summary,
            "conteo_por_estado": status_counts
        }

    def get_bill_detail(self, bill_id: int) -> BillDetailSchema:
        bill = self.db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            raise HTTPException(status_code=404, detail="Factura no encontrada")

        user = bill.user
        concepts = self.db.query(BillConcept).filter(BillConcept.bill_id == bill.id).all()
        transaction = bill.transaction

        return BillDetailSchema(
            bill_number=bill.bill_number,
            emission_date=bill.emission_date,
            due_date=bill.due_date,
            payment_interval=bill.payment_interval,
            total_amount=bill.amount_due,
            status=bill.status,
            client_name=user.name,
            client_document=user.document_number,
            client_email=user.email,
            property_id=bill.property_id,
            lot_id=bill.lot_id,
            concepts=[ConceptSchema.from_orm(c) for c in concepts],
            payment_method=transaction.payment_method if transaction else None,
            payment_reference=transaction.payment_reference if transaction else None,
            transaction_value=transaction.payment_value if transaction else None,
            payment_date=transaction.payment_date if transaction else None,
        )

    def get_bills_by_user(self, document_number: str):
        user = self.db.query(User).filter(User.document_number == document_number).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        bills = self.db.query(Bill).filter(Bill.user_id == user.id).all()

        summary = [
            BillSummarySchema(
                bill_number=b.bill_number,
                property_id=b.property_id,
                lot_id=b.lot_id,
                user_document=user.document_number,
                payment_interval=b.payment_interval,
                emission_date=b.emission_date,
                due_date=b.due_date,
                amount_due=b.amount_due,
                status=b.status,
            )
            for b in bills
        ]

        # Conteo por estado
        status_counts = {}
        for b in bills:
            status_counts[b.status] = status_counts.get(b.status, 0) + 1

        return {
            "facturas": summary,
            "conteo_por_estado": status_counts
        }

    def get_all_transactions(self) -> List[TransactionSummarySchema]:
        transactions = self.db.query(Transaction).all()
        return [
            TransactionSummarySchema(
                bill_number=t.bill.bill_number,
                user_document=t.bill.user.document_number,
                payment_date=t.payment_date,
                payment_reference=t.payment_reference,
                payment_method=t.payment_method,
                payment_value=t.payment_value,
                payment_status=t.payment_status,
            )
            for t in transactions
        ]

    def get_transaction_detail(self, transaction_id: int) -> TransactionDetailSchema:
        transaction = self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            raise HTTPException(status_code=404, detail="Transacción no encontrada")

        return TransactionDetailSchema(
            payment_method=transaction.payment_method,
            payer_name=transaction.payer_name,
            transaction_value=transaction.payment_value,
            payment_status=transaction.payment_status,
            payment_date=transaction.payment_date,
            payment_reference=transaction.payment_reference,
            email=transaction.email,
        )
