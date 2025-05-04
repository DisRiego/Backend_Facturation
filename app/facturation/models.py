from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Float, DECIMAL, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Vars(Base):
    __tablename__ = 'vars'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    description = Column(String(100))

class Property(Base):
    __tablename__ = 'property'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60))
    latitude = Column(DECIMAL(20, 9))
    longitude = Column(DECIMAL(20, 9))
    extension = Column(DECIMAL(20, 2))
    real_estate_registration_number = Column(Integer)
    public_deed = Column(String(255))
    freedom_tradition_certificate = Column(String(255))
    State = Column(Integer, ForeignKey('vars.id'), default=3)
    
    # Relationships
    lots = relationship("PropertyLot", back_populates="property")
    users = relationship("UserProperty", back_populates="property")
    state_ref = relationship("Vars", foreign_keys=[State])

class Lot(Base):
    __tablename__ = 'lot'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60))
    real_estate_registration_number = Column(String(255))
    extension = Column(DECIMAL(20, 2))
    latitude = Column(DECIMAL(20, 9))
    longitude = Column(DECIMAL(20, 9))
    public_deed = Column(String(255))
    freedom_tradition_certificate = Column(String(255))
    payment_interval = Column(Integer, ForeignKey('payment_interval.id'))
    type_crop_id = Column(Integer, ForeignKey('type_crop.id'))
    planting_date = Column(Date)
    estimated_harvest_date = Column(Date)
    State = Column(Integer, ForeignKey('vars.id'), default=5)
    
    # Relationships
    properties = relationship("PropertyLot", back_populates="lot")
    consumptions = relationship("Consumption", back_populates="lot")
    type_crop = relationship("TypeCrop", back_populates="lots")
    payment_interval_ref = relationship("PaymentInterval", foreign_keys=[payment_interval])
    state_ref = relationship("Vars", foreign_keys=[State])

class PropertyLot(Base):
    __tablename__ = 'property_lot'
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey('property.id'))
    lot_id = Column(Integer, ForeignKey('lot.id'))
    
    # Relationships
    property = relationship("Property", back_populates="lots")
    lot = relationship("Lot", back_populates="properties")

class Consumption(Base):
    __tablename__ = 'consumption'
    
    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey('lot.id'), nullable=False)
    consumption_date = Column(Date)
    registered_consumption = Column(Integer)
    projected_consumption = Column(Date)
    
    # Relationships
    lot = relationship("Lot", back_populates="consumptions")

class TypeCrop(Base):
    __tablename__ = 'type_crop'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60))
    harvest_time = Column(Integer, default=0, nullable=False)
    payment_interval_id = Column(Integer, ForeignKey('payment_interval.id'), nullable=False)
    state_id = Column(Integer, ForeignKey('vars.id'), default=7)
    
    # Relationships
    lots = relationship("Lot", back_populates="type_crop")
    payment_interval = relationship("PaymentInterval", back_populates="type_crops")
    state = relationship("Vars", foreign_keys=[state_id])

class PaymentInterval(Base):
    __tablename__ = 'payment_interval'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128))
    interval_days = Column(Integer, default=0, nullable=False)
    
    # Relationships
    type_crops = relationship("TypeCrop", back_populates="payment_interval")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60))
    first_last_name = Column(String(60))
    second_last_name = Column(String(60))
    type_document_id = Column(Integer, ForeignKey('type_document.id'))
    document_number = Column(Integer, unique=True)
    date_issuance_document = Column(DateTime)
    type_person_id = Column(Integer, ForeignKey('type_person.id'))
    birthday = Column(DateTime)
    address = Column(String(100))
    gender_id = Column(Integer, ForeignKey('gender.id'))
    profile_picture = Column(String(255))
    phone = Column(String(20))
    email = Column(String(50), unique=True)
    password = Column(Text)
    status_id = Column(Integer, ForeignKey('status_user.id'))
    email_status = Column(Boolean)
    password_salt = Column(Text)
    country = Column(String(50))
    department = Column(String(255))
    city = Column(Integer)
    extension_phone = Column(String)
    first_login_complete = Column(Boolean, default=False)
    last_pre_register_attempt = Column(DateTime)
    pre_register_attempts = Column(Integer, default=0)
    
    # Relationships
    properties = relationship("UserProperty", back_populates="user")

class UserProperty(Base):
    __tablename__ = 'user_property'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    property_id = Column(Integer, ForeignKey('property.id'))
    
    # Relationships
    user = relationship("User", back_populates="properties")
    property = relationship("Property", back_populates="users")

# Additional models for consumption measurement and request functionality
class Request(Base):
    __tablename__ = 'request'
    
    id = Column(Integer, primary_key=True, index=True)
    type_opening_id = Column(Integer, ForeignKey('type_opening.id'))
    status = Column(Integer, ForeignKey('vars.id'))
    lot_id = Column(Integer, ForeignKey('lot.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    device_iot_id = Column(Integer, ForeignKey('device_iot.id'))
    open_date = Column(DateTime)
    close_date = Column(DateTime)
    request_date = Column(DateTime)
    volume_water = Column(Integer)
    
    # Relationships
    consumption_measurements = relationship("ConsumptionMeasurement", back_populates="request")

class ConsumptionMeasurement(Base):
    __tablename__ = 'consumption_measurements'
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey('request.id'), nullable=False)
    final_volume = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    request = relationship("Request", back_populates="consumption_measurements")

# For AI predictions - additional model for storing projected consumptions
class ConsumptionProjection(Base):
    __tablename__ = 'consumption_projection'
    
    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey('lot.id'), nullable=False)
    projection_date = Column(Date, nullable=False)
    projected_consumption = Column(Float, nullable=False)
    actual_consumption = Column(Float, nullable=True)
    variation = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    lot = relationship("Lot")