from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# Base Schemas
class VarsBase(BaseModel):
    name: str = Field(..., max_length=255)
    type: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=100)

class VarsResponse(VarsBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# Property Schemas
class PropertyBase(BaseModel):
    name: str = Field(..., max_length=60)
    latitude: Optional[Decimal] = Field(None, max_digits=20, decimal_places=9)
    longitude: Optional[Decimal] = Field(None, max_digits=20, decimal_places=9)
    extension: Optional[Decimal] = Field(None, max_digits=20, decimal_places=2)
    real_estate_registration_number: Optional[int] = None
    public_deed: Optional[str] = Field(None, max_length=255)
    freedom_tradition_certificate: Optional[str] = Field(None, max_length=255)

class PropertyResponse(PropertyBase):
    id: int
    State: int
    
    model_config = ConfigDict(from_attributes=True)

# Type Crop Schemas
class TypeCropBase(BaseModel):
    name: str = Field(..., max_length=60)
    harvest_time: int = Field(default=0)

class TypeCropResponse(TypeCropBase):
    id: int
    payment_interval_id: int
    state_id: int
    
    model_config = ConfigDict(from_attributes=True)

# Lot Schemas
class LotBase(BaseModel):
    name: str = Field(..., max_length=60)
    extension: Optional[Decimal] = Field(None, max_digits=20, decimal_places=2)
    type_crop_id: Optional[int] = None

class LotResponse(LotBase):
    id: int
    real_estate_registration_number: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    payment_interval: Optional[int] = None
    planting_date: Optional[date] = None
    estimated_harvest_date: Optional[date] = None
    State: int
    type_crop: Optional[TypeCropResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

class LotConsumptionDetail(LotResponse):
    registered_consumption: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

# Property with Lots Response
class PropertyWithLotsResponse(PropertyResponse):
    lots: List[LotResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

# Consumption Schemas
class ConsumptionBase(BaseModel):
    lot_id: int
    consumption_date: Optional[date] = None
    registered_consumption: Optional[int] = None
    projected_consumption: Optional[date] = None

class ConsumptionResponse(ConsumptionBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# Consumption Projection Schemas
class ConsumptionProjectionBase(BaseModel):
    lot_id: int
    projection_date: date
    projected_consumption: float
    actual_consumption: Optional[float] = None
    variation: Optional[float] = None

class ConsumptionProjectionResponse(ConsumptionProjectionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Filter Schemas for searches
class ConsumptionFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    payment_interval: Optional[str] = None
    registered_consumption_min: Optional[float] = None
    registered_consumption_max: Optional[float] = None
    search: Optional[str] = None

# Dashboard Schemas for Requerimiento 6 (Gestión de consumo)
class ConsumptionDashboardResponse(BaseModel):
    total_consumption_m3: float = Field(..., description="Consumos totales en m³")
    average_monthly_consumption: float = Field(..., description="Consumo promedio mensual")
    average_monthly_projected: float = Field(..., description="Consumo promedio mensual proyectado")
    expected_variation: float = Field(..., description="Variación esperada")
    year: int = Field(..., description="Año seleccionado")
    
    model_config = ConfigDict(from_attributes=True)

class ConsumptionGraphData(BaseModel):
    month: str
    registered_consumption: float
    projected_consumption: float
    
    model_config = ConfigDict(from_attributes=True)

class ConsumptionListItem(BaseModel):
    id: int
    property_id: int
    property_name: str
    lot_id: int
    lot_name: str
    extension_m2: Decimal
    payment_interval: str
    start_date: date
    end_date: date
    registered_consumption_m3: float
    
    model_config = ConfigDict(from_attributes=True)

class ConsumptionManagementResponse(BaseModel):
    dashboard: ConsumptionDashboardResponse
    consumption_graph: List[ConsumptionGraphData]
    consumption_list: List[ConsumptionListItem]
    
    model_config = ConfigDict(from_attributes=True)

# Dashboard Schemas for Requerimiento 7 (Consumo de mis predios y lotes)
class MyConsumptionDashboardResponse(BaseModel):
    total_consumption_m3: float = Field(..., description="Consumos totales en m³")
    average_monthly_consumption: float = Field(..., description="Consumo promedio mensual")
    average_monthly_projected: float = Field(..., description="Consumo promedio mensual proyectado")
    expected_variation: float = Field(..., description="Variación esperada")
    year: int = Field(..., description="Año seleccionado")
    
    model_config = ConfigDict(from_attributes=True)

class PropertyConsumptionListItem(BaseModel):
    property_id: int
    property_name: str
    extension_m2: Decimal
    start_date: date
    end_date: date
    registered_consumption_m3: float
    
    model_config = ConfigDict(from_attributes=True)

class LotListItem(BaseModel):
    lot_id: int
    lot_name: str
    extension_m2: Decimal
    type_crop: str
    registered_consumption_m3: float
    
    model_config = ConfigDict(from_attributes=True)

class PropertyWithLots(BaseModel):
    property_id: int
    property_name: str
    lots: List[LotListItem]
    
    model_config = ConfigDict(from_attributes=True)

class LotDetailView(BaseModel):
    lot_id: int
    lot_name: str
    property_name: str
    type_crop: str
    dashboard: MyConsumptionDashboardResponse
    consumption_graph: List[ConsumptionGraphData]
    consumption_list: List[ConsumptionListItem]
    
    model_config = ConfigDict(from_attributes=True)

class MyConsumptionResponse(BaseModel):
    dashboard: MyConsumptionDashboardResponse
    consumption_graph: List[ConsumptionGraphData]
    property_list: List[PropertyConsumptionListItem]
    
    model_config = ConfigDict(from_attributes=True)

# Report Generation Schemas
class ConsumptionReportRequest(BaseModel):
    filters: ConsumptionFilter
    report_type: str = Field(..., pattern="^(general|property|lot)$")
    format: str = Field(default="pdf", pattern="^(pdf|excel)$")
    lot_id: Optional[int] = None
    property_id: Optional[int] = None

class ConsumptionReportResponse(BaseModel):
    file_url: str
    file_name: str
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Prediction Schemas for AI Integration
class ConsumptionPredictionRequest(BaseModel):
    lot_id: int
    start_date: date
    end_date: date
    
    model_config = ConfigDict(from_attributes=True)

class ConsumptionPredictionResponse(BaseModel):
    lot_id: int
    predictions: List[ConsumptionProjectionResponse]
    
    model_config = ConfigDict(from_attributes=True)

# Generic Response
class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)