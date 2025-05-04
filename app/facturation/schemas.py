from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from typing import Dict

# ----------------------------
# Conceptos dentro de la factura
# ----------------------------

class ConceptSchema(BaseModel):
    concept_name: str
    concept_detail: Optional[str]
    unit_value: float
    quantity: int
    total_value: float

    class Config:
        orm_mode = True

# ----------------------------
# Resumen de factura (GET /bills, /bills/user/{})
# ----------------------------

class BillSummarySchema(BaseModel):
    bill_number: str
    property_id: int
    lot_id: int
    user_document: str
    payment_interval: str
    emission_date: date
    due_date: date
    amount_due: float
    status: str

    class Config:
        orm_mode = True
        
class BillsWithStatusCountSchema(BaseModel):
    facturas: List[BillSummarySchema]
    conteo_por_estado: Dict[str, int]

    class Config:
        orm_mode = True
        
# ----------------------------
# Detalle de factura (GET /bills/{id})
# ----------------------------

class BillDetailSchema(BaseModel):
    bill_number: str
    emission_date: date
    due_date: date
    payment_interval: str
    total_amount: float
    status: str
    client_name: str
    client_document: str
    client_email: Optional[str]
    property_id: int
    lot_id: int
    concepts: List[ConceptSchema]
    
    # Campos exclusivos si está pagada
    payment_method: Optional[str]
    payment_reference: Optional[str]
    transaction_value: Optional[float]
    payment_date: Optional[date]

    class Config:
        orm_mode = True

# ----------------------------
# Resumen de transacción (GET /transactions)
# ----------------------------

class TransactionSummarySchema(BaseModel):
    bill_number: str
    user_document: str
    payment_date: date
    payment_reference: str
    payment_method: str
    payment_value: float
    payment_status: str

    class Config:
        orm_mode = True

# ----------------------------
# Detalle de transacción (GET /transactions/{id})
# ----------------------------

class TransactionDetailSchema(BaseModel):
    payment_method: str
    payer_name: str
    transaction_value: float
    payment_status: str
    payment_date: date
    payment_reference: str
    email: Optional[str]

    class Config:
        orm_mode = True

