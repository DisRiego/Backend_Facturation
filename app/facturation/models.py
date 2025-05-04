from sqlalchemy import TIMESTAMP, Column, Date, Integer, String, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Vars(Base):
    __tablename__ = 'vars'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(String(50), nullable=False)  # tipo de evento
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)
    action_type = Column(String(50))  # crear, editar, habilitar, etc.
    entity_type = Column(String(50))  # concepto, factura, transaccion
    entity_id = Column(Integer)  # ID de la entidad relacionada
    
    # Relación con el usuario
    user = relationship("User", back_populates="notifications")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(60), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    role = Column(String(20), nullable=False)  # cliente, administrador
    receive_notifications = Column(Boolean, default=True)
    
    # Relación con notificaciones
    notifications = relationship("Notification", back_populates="user")
