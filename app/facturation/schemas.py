from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class NotificationBase(BaseModel):
    type: str
    title: str
    message: str
    action_type: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    created_at: datetime
    read: bool
    
    class Config:
        from_attributes = True

class NotificationList(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int

class MarkNotificationRead(BaseModel):
    notification_id: int
    read: bool = True
