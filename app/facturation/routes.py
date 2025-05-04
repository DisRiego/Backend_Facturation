from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, extract
from app.database import get_db
from app.facturation.services import ConsumptionService
from app.facturation.schemas import (
    ConsumptionFilter,
    ConsumptionManagementResponse,
    MyConsumptionResponse,
    LotListItem,
    LotDetailView,
    ConsumptionReportRequest,
    ConsumptionReportResponse,
    StandardResponse
)
from app.facturation.models import Consumption, Property, Lot

router = APIRouter(prefix="/consumption", tags=["Consumption"])

# Requerimiento 6: Gestión de consumo (Admin)
@router.get("/management", response_model=ConsumptionManagementResponse)
def get_consumption_management(
    year: int = Query(default=datetime.now().year, description="Año para consultar"),
    start_date: Optional[date] = Query(None, description="Fecha inicial del filtro"),
    end_date: Optional[date] = Query(None, description="Fecha final del filtro"),
    payment_interval: Optional[str] = Query(None, description="Intervalo de pago"),
    registered_consumption_min: Optional[float] = Query(None, description="Consumo mínimo"),
    registered_consumption_max: Optional[float] = Query(None, description="Consumo máximo"),
    search: Optional[str] = Query(None, description="Búsqueda por nombre de predio o lote"),
    db: Session = Depends(get_db)
):
    """
    Obtener datos de gestión de consumo para administradores.
    """
    try:
        consumption_service = ConsumptionService(db)
        
        filters = ConsumptionFilter(
            start_date=start_date,
            end_date=end_date,
            payment_interval=payment_interval,
            registered_consumption_min=registered_consumption_min,
            registered_consumption_max=registered_consumption_max,
            search=search
        )
        
        result = consumption_service.get_consumption_management(year, filters)
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la gestión de consumo: {str(e)}"
        )

# Requerimiento 7: Consumo de mis predios y lotes (Usuario)
@router.get("/my-consumption", response_model=MyConsumptionResponse)
def get_my_consumption(
    user_id: int = Query(..., description="ID del usuario"),
    year: int = Query(default=datetime.now().year, description="Año para consultar"),
    start_date: Optional[date] = Query(None, description="Fecha inicial del filtro"),
    end_date: Optional[date] = Query(None, description="Fecha final del filtro"),
    registered_consumption_min: Optional[float] = Query(None, description="Consumo mínimo"),
    registered_consumption_max: Optional[float] = Query(None, description="Consumo máximo"),
    search: Optional[str] = Query(None, description="Búsqueda por nombre de predio"),
    db: Session = Depends(get_db)
):
    """
    Obtener datos de consumo personal del usuario para sus predios y lotes.
    """
    try:
        consumption_service = ConsumptionService(db)
        
        filters = ConsumptionFilter(
            start_date=start_date,
            end_date=end_date,
            registered_consumption_min=registered_consumption_min,
            registered_consumption_max=registered_consumption_max,
            search=search
        )
        
        result = consumption_service.get_my_consumption(user_id, year, filters)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el consumo personal: {str(e)}"
        )

@router.get("/property/{property_id}/lots", response_model=List[LotListItem])
def get_property_lots(
    property_id: int,
    user_id: int = Query(..., description="ID del usuario"),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de lotes de una propiedad específica.
    """
    try:
        consumption_service = ConsumptionService(db)
        lots = consumption_service.get_property_lots(property_id, user_id)
        return lots
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los lotes de la propiedad: {str(e)}"
        )

@router.get("/lot/{lot_id}/detail", response_model=LotDetailView)
def get_lot_detail(
    lot_id: int,
    user_id: int = Query(..., description="ID del usuario"),
    year: int = Query(default=datetime.now().year, description="Año para consultar"),
    start_date: Optional[date] = Query(None, description="Fecha inicial del filtro"),
    end_date: Optional[date] = Query(None, description="Fecha final del filtro"),
    registered_consumption_min: Optional[float] = Query(None, description="Consumo mínimo"),
    registered_consumption_max: Optional[float] = Query(None, description="Consumo máximo"),
    search: Optional[str] = Query(None, description="Búsqueda"),
    db: Session = Depends(get_db)
):
    """
    Obtener detalle de consumo de un lote específico.
    """
    try:
        consumption_service = ConsumptionService(db)
        
        filters = ConsumptionFilter(
            start_date=start_date,
            end_date=end_date,
            registered_consumption_min=registered_consumption_min,
            registered_consumption_max=registered_consumption_max,
            search=search
        )
        
        result = consumption_service.get_lot_detail_consumption(
            lot_id, 
            user_id, 
            year, 
            filters
        )
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el detalle del lote: {str(e)}"
        )

# Endpoints para generación de reportes
@router.post("/report/generate", response_model=ConsumptionReportResponse)
def generate_consumption_report(
    request: ConsumptionReportRequest,
    user_id: int = Query(..., description="ID del usuario"),
    db: Session = Depends(get_db)
):
    """
    Generar reporte de consumo en PDF o Excel.
    """
    try:
        consumption_service = ConsumptionService(db)
        
        # Verificar que el usuario tenga acceso a los datos solicitados
        if request.report_type == "lot" and request.lot_id:
            # Verificar acceso al lote
            consumption_service.get_lot_detail_consumption(
                request.lot_id, 
                user_id, 
                datetime.now().year, 
                request.filters
            )
        elif request.report_type == "property" and request.property_id:
            # Verificar acceso a la propiedad
            consumption_service.get_property_lots(
                request.property_id, 
                user_id
            )
        
        result = consumption_service.generate_consumption_report(
            request, 
            user_id
        )
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el reporte: {str(e)}"
        )

# Endpoints para predicciones de consumo (integración con IA)
@router.get("/predictions", response_model=dict)
def get_consumption_predictions(
    lot_id: Optional[int] = Query(None, description="ID del lote para predicción específica"),
    start_date: date = Query(..., description="Fecha inicial para predicción"),
    end_date: date = Query(..., description="Fecha final para predicción"),
    db: Session = Depends(get_db)
):
    """
    Obtener predicciones de consumo basadas en IA.
    """
    try:
        # TODO: Implementar integración con el servicio de IA
        return {
            "message": "Endpoint para predicciones de consumo - Pendiente de implementación",
            "lot_id": lot_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener predicciones: {str(e)}"
        )

# Endpoint adicional para dashboard administrativo
@router.get("/admin/dashboard", response_model=dict)
def get_admin_dashboard(
    year: int = Query(default=datetime.now().year, description="Año para el dashboard"),
    db: Session = Depends(get_db)
):
    """
    Obtener dashboard administrativo de consumo.
    """
    try:
        # Obtener métricas generales
        total_consumption = db.query(func.sum(Consumption.registered_consumption))\
            .filter(extract('year', Consumption.consumption_date) == year)\
            .scalar() or 0
        
        # Obtener número de propiedades activas
        active_properties = db.query(func.count(Property.id))\
            .filter(Property.State == 5)\
            .scalar() or 0
        
        # Obtener número de lotes activos
        active_lots = db.query(func.count(Lot.id))\
            .filter(Lot.State == 5)\
            .scalar() or 0
        
        return {
            "year": year,
            "total_consumption_m3": float(total_consumption),
            "active_properties": active_properties,
            "active_lots": active_lots,
            "last_updated": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el dashboard administrativo: {str(e)}"
        )

# Endpoint para consumo histórico
@router.get("/historical/{lot_id}", response_model=List[dict])
def get_historical_consumption(
    lot_id: int,
    user_id: int = Query(..., description="ID del usuario"),
    months: int = Query(default=12, ge=1, le=36, description="Número de meses históricos"),
    db: Session = Depends(get_db)
):
    """
    Obtener consumo histórico de un lote.
    """
    try:
        consumption_service = ConsumptionService(db)
        
        # Verificar acceso al lote
        consumption_service.get_lot_detail_consumption(
            lot_id,
            user_id,
            datetime.now().year,
            ConsumptionFilter()
        )
        
        # Obtener datos históricos
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30 * months)
        
        historical_data = db.query(
            Consumption.consumption_date,
            Consumption.registered_consumption
        ).filter(
            Consumption.lot_id == lot_id,
            Consumption.consumption_date >= start_date,
            Consumption.consumption_date <= end_date
        ).order_by(
            Consumption.consumption_date
        ).all()
        
        return [
            {
                "date": record.consumption_date.isoformat(),
                "registered": float(record.registered_consumption) if record.registered_consumption else 0
            }
            for record in historical_data
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el consumo histórico: {str(e)}"
        )

# Endpoint para obtener consumo por propiedad
@router.get("/property/{property_id}/consumption", response_model=dict)
def get_property_consumption(
    property_id: int,
    user_id: int = Query(..., description="ID del usuario"),
    year: int = Query(default=datetime.now().year, description="Año para consultar"),
    db: Session = Depends(get_db)
):
    """
    Obtener consumo total de una propiedad.
    """
    try:
        consumption_service = ConsumptionService(db)
        
        # Verificar acceso a la propiedad
        consumption_service.get_property_lots(property_id, user_id)
        
        # Obtener consumo total de la propiedad
        total_consumption = db.query(
            func.sum(Consumption.registered_consumption)
        ).join(
            Lot, Consumption.lot_id == Lot.id
        ).join(
            PropertyLot, Lot.id == PropertyLot.lot_id
        ).filter(
            PropertyLot.property_id == property_id,
            extract('year', Consumption.consumption_date) == year
        ).scalar() or 0
        
        # Obtener consumo por mes
        monthly_consumption = db.query(
            extract('month', Consumption.consumption_date).label('month'),
            func.sum(Consumption.registered_consumption).label('total')
        ).join(
            Lot, Consumption.lot_id == Lot.id
        ).join(
            PropertyLot, Lot.id == PropertyLot.lot_id
        ).filter(
            PropertyLot.property_id == property_id,
            extract('year', Consumption.consumption_date) == year
        ).group_by(
            extract('month', Consumption.consumption_date)
        ).all()
        
        months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        monthly_data = {months[int(record.month) - 1]: float(record.total) if record.total else 0 
                       for record in monthly_consumption}
        
        return {
            "property_id": property_id,
            "year": year,
            "total_consumption": float(total_consumption),
            "monthly_consumption": monthly_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el consumo de la propiedad: {str(e)}"
        )