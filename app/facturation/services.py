from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, event
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.facturation.models import Vars
from app.facturation.models import Notification, User
from app.facturation.schemas import NotificationCreate, NotificationResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sistema de Notificaciones Integrado
class NotificationSystem:
    """Sistema de notificaciones automáticas integrado en facturation"""
    
    @staticmethod
    def create_notification(db: Session, user_id: int, notification_type: str, 
                          title: str, message: str, entity_type: str = None, 
                          entity_id: int = None, action_type: str = None):
        """Crear una notificación en la base de datos"""
        try:
            notification_data = {
                'user_id': user_id,
                'type': notification_type,
                'title': title,
                'message': message,
                'created_at': datetime.utcnow(),
                'read': False,
                'action_type': action_type,
                'entity_type': entity_type,
                'entity_id': entity_id
            }
            
            query = text("""
                INSERT INTO notifications 
                (user_id, type, title, message, created_at, read, 
                 action_type, entity_type, entity_id)
                VALUES 
                (:user_id, :type, :title, :message, :created_at, :read,
                 :action_type, :entity_type, :entity_id)
                RETURNING id
            """)
            
            result = db.execute(query, notification_data)
            notification_id = result.scalar()
            db.commit()
            
            logger.info(f"Notificación creada: {notification_id}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Error creando notificación: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def notify_concept_action(db: Session, user_id: int, action: str, 
                            concept_id: int, concept_name: str):
        """Notificar acciones sobre conceptos"""
        actions_text = {
            "crear": "creado",
            "editar": "editado", 
            "habilitar": "habilitado",
            "inhabilitar": "inhabilitado"
        }
        
        title = f"Concepto {actions_text.get(action, action)}"
        message = f"El concepto '{concept_name}' ha sido {actions_text.get(action, action)}."
        
        return NotificationSystem.create_notification(
            db, user_id, "concepto", title, message, 
            "concepto", concept_id, action
        )
    
    @staticmethod
    def notify_invoice_action(db: Session, user_id: int, action: str, 
                            invoice_id: int, invoice_number: str):
        """Notificar acciones sobre facturas"""
        messages = {
            "generacion": f"Se ha generado la factura {invoice_number}.",
            "pago": f"Se ha registrado el pago de la factura {invoice_number}.",
            "vencimiento": f"La factura {invoice_number} está próxima a vencer."
        }
        
        title = f"Factura - {action.title()}"
        message = messages.get(action, f"Acción realizada en factura {invoice_number}")
        
        return NotificationSystem.create_notification(
            db, user_id, "factura", title, message, 
            "factura", invoice_id, action
        )
    
    @staticmethod
    def notify_transaction_action(db: Session, user_id: int, action: str, 
                                transaction_id: int):
        """Notificar acciones sobre transacciones"""
        messages = {
            "aprobacion": "Su transacción ha sido aprobada.",
            "rechazo": "Su transacción ha sido rechazada."
        }
        
        title = f"Transacción - {action.title()}"
        message = messages.get(action, "Se ha actualizado el estado de su transacción.")
        
        return NotificationSystem.create_notification(
            db, user_id, "transaccion", title, message, 
            "transaccion", transaction_id, action
        )
    
    @staticmethod
    def notify_upcoming_due(db: Session, user_id: int, days_until_due: int, 
                          invoice_id: int, invoice_number: str):
        """Notificar próximo vencimiento"""
        if days_until_due == 7:
            message = f"La factura {invoice_number} vencerá en 1 semana."
        elif days_until_due == 1:
            message = f"La factura {invoice_number} vencerá mañana."
        else:
            message = f"La factura {invoice_number} vencerá en {days_until_due} días."
        
        return NotificationSystem.create_notification(
            db, user_id, "alerta_vencimiento", "Alerta de vencimiento", 
            message, "factura", invoice_id, f"{days_until_due}_dias_antes"
        )


class FacturationService:
    # Variable de clase para el scheduler
    _scheduler = None
    _scheduler_started = False
    
    def __init__(self, db: Session):
        self.db = db
        self._setup_scheduler()
    
    @classmethod
    def _setup_scheduler(cls):
        """Configurar el scheduler para tareas programadas"""
        if not cls._scheduler:
            cls._scheduler = BackgroundScheduler()
            
            # Agregar tarea para verificar vencimientos diariamente a las 8:00 AM
            cls._scheduler.add_job(
                cls.check_upcoming_due_dates,
                trigger=CronTrigger(hour=8, minute=0),
                id='check_due_dates',
                replace_existing=True
            )
            
            if not cls._scheduler_started:
                cls._scheduler.start()
                cls._scheduler_started = True
                logger.info("Scheduler de notificaciones iniciado")
    
    @classmethod
    def check_upcoming_due_dates(cls):
        """Verificar facturas próximas a vencer"""
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            today = datetime.now().date()
            week_from_now = today + timedelta(days=7)
            tomorrow = today + timedelta(days=1)
            
            query_week = text("""
                SELECT id, user_id, number 
                FROM invoices 
                WHERE due_date = :due_date 
                AND status != 'paid'
            """)
            
            invoices_week = db.execute(query_week, {'due_date': week_from_now}).fetchall()
            
            for invoice in invoices_week:
                NotificationSystem.notify_upcoming_due(
                    db, invoice.user_id, 7, invoice.id, invoice.number
                )
            
            invoices_tomorrow = db.execute(
                query_week, {'due_date': tomorrow}
            ).fetchall()
            
            for invoice in invoices_tomorrow:
                NotificationSystem.notify_upcoming_due(
                    db, invoice.user_id, 1, invoice.id, invoice.number
                )
            
            db.commit()
            logger.info("Verificación de vencimientos completada")
        except Exception as e:
            logger.error(f"Error en verificación de vencimientos: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_facturation(self):
        """Obtener todos los facturacion"""
        try:
            # Obtener todos los facturacions con el query
            facturation = self.db.query(Vars).all()

            if not facturation:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Facturacion",
                            "message": "No se encontraron facturacion."
                        }
                    }
                )

            # Convertir la respuesta a un formato JSON válido
            facturation_data = jsonable_encoder(facturation)

            return JSONResponse(
                status_code=200,
                content={"success": True, "data": facturation_data}
            )
        except Exception as e:
            # Aquí capturamos cualquier excepción inesperada
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener facturacion",
                        "message": f"Ocurrió un error al intentar obtener los facturacion: {str(e)}"
                    }
                }
            )

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_notification(self, notification_data: NotificationCreate) -> NotificationResponse:
        """Crear una nueva notificación"""
        # Verificar que el usuario existe y tiene permisos para recibir notificaciones
        user = self.db.query(User).filter(User.id == notification_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if not user.receive_notifications:
            raise HTTPException(status_code=403, detail="Usuario no tiene permisos para recibir notificaciones")
        
        # Crear la notificación
        notification = Notification(**notification_data.dict())
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        return NotificationResponse.from_orm(notification)
    
    def get_user_notifications(self, user_id: int, skip: int = 0, limit: int = 50) -> dict:
        """Obtener notificaciones de un usuario"""
        # Verificar que el usuario existe
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Obtener notificaciones
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        total = query.count()
        notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
        unread_count = query.filter(Notification.read == False).count()
        
        return {
            "notifications": [NotificationResponse.from_orm(n) for n in notifications],
            "total": total,
            "unread_count": unread_count
        }
    
    def mark_notification_as_read(self, notification_id: int, user_id: int) -> NotificationResponse:
        """Marcar una notificación como leída"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notificación no encontrada")
        
        notification.read = True
        self.db.commit()
        self.db.refresh(notification)
        
        return NotificationResponse.from_orm(notification)
    
    def create_concept_notification(self, user_id: int, action: str, concept_id: int, concept_name: str):
        """Crear notificación para acciones sobre conceptos"""
        actions_text = {
            "crear": "creado",
            "editar": "editado", 
            "habilitar": "habilitado",
            "inhabilitar": "inhabilitado"
        }
        
        notification_data = NotificationCreate(
            user_id=user_id,
            type="concepto",
            title=f"Concepto {actions_text.get(action, action)}",
            message=f"El concepto '{concept_name}' ha sido {actions_text.get(action, action)}.",
            action_type=action,
            entity_type="concepto",
            entity_id=concept_id
        )
        
        return self.create_notification(notification_data)
    
    def create_invoice_notification(self, user_id: int, action: str, invoice_id: int, invoice_number: str):
        """Crear notificación para acciones sobre facturas"""
        messages = {
            "generacion": f"Se ha generado la factura {invoice_number}.",
            "pago": f"Se ha registrado el pago de la factura {invoice_number}.",
            "vencimiento": f"La factura {invoice_number} está próxima a vencer."
        }
        
        notification_data = NotificationCreate(
            user_id=user_id,
            type="factura",
            title=f"Factura - {action.title()}",
            message=messages.get(action, f"Acción realizada en factura {invoice_number}"),
            action_type=action,
            entity_type="factura",
            entity_id=invoice_id
        )
        
        return self.create_notification(notification_data)
    
    def create_transaction_notification(self, user_id: int, action: str, transaction_id: int):
        """Crear notificación para transacciones"""
        messages = {
            "aprobacion": "Su transacción ha sido aprobada.",
            "rechazo": "Su transacción ha sido rechazada."
        }
        
        notification_data = NotificationCreate(
            user_id=user_id,
            type="transaccion",
            title=f"Transacción - {action.title()}",
            message=messages.get(action, "Se ha actualizado el estado de su transacción."),
            action_type=action,
            entity_type="transaccion",
            entity_id=transaction_id
        )
        
        return self.create_notification(notification_data)
    
    def create_upcoming_due_notification(self, user_id: int, days_until_due: int, invoice_id: int, invoice_number: str):
        """Crear notificación para alerta de próximo vencimiento"""
        if days_until_due == 7:
            message = f"La factura {invoice_number} vencerá en 1 semana."
        elif days_until_due == 1:
            message = f"La factura {invoice_number} vencerá mañana."
        else:
            message = f"La factura {invoice_number} vencerá en {days_until_due} días."
        
        notification_data = NotificationCreate(
            user_id=user_id,
            type="alerta_vencimiento",
            title="Alerta de vencimiento",
            message=message,
            action_type=f"{days_until_due}_dias_antes",
            entity_type="factura",
            entity_id=invoice_id
        )
        
        return self.create_notification(notification_data)