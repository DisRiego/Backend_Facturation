from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Vars(Base):  # Por si se necesita para estados
    __tablename__ = 'vars'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    document_number = Column(String, nullable=False)
    email = Column(String, nullable=True)

class Property(Base):
    __tablename__ = 'property'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

class Lot(Base):
    __tablename__ = 'lot'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

class PropertyLot(Base):
    __tablename__ = 'property_lot'
    property_id = Column(Integer, ForeignKey('property.id'), primary_key=True)
    lot_id = Column(Integer, ForeignKey('lot.id'), primary_key=True)

class PropertyUser(Base):
    __tablename__ = 'user_property'
    property_id = Column(Integer, ForeignKey('property.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    property = relationship("Property", backref="property_users")
    user = relationship("User", backref="property_users")

# ----------------------------
# NUEVAS TABLAS: Facturación
# ----------------------------

class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, index=True)
    bill_number = Column(String, nullable=False, unique=True)
    property_id = Column(Integer, ForeignKey("property.id"))
    lot_id = Column(Integer, ForeignKey("lot.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    payment_interval = Column(String, nullable=False)
    emission_date = Column(Date)
    due_date = Column(Date)
    amount_due = Column(Float)
    status = Column(String)

    property = relationship("Property")
    lot = relationship("Lot")
    user = relationship("User")
    concepts = relationship("BillConcept", back_populates="bill")
    transaction = relationship("Transaction", back_populates="bill", uselist=False)

class BillConcept(Base):
    __tablename__ = "bill_concepts"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    concept_name = Column(String)
    concept_detail = Column(String)
    unit_value = Column(Float)
    quantity = Column(Integer)
    total_value = Column(Float)

    bill = relationship("Bill", back_populates="concepts")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    payment_method = Column(String)
    payer_name = Column(String)
    payment_value = Column(Float)
    payment_status = Column(String)
    payment_date = Column(Date)
    payment_reference = Column(String)
    email = Column(String)

    bill = relationship("Bill", back_populates="transaction")
