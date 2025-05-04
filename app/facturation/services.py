from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, extract
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from app.facturation.models import (
    Consumption, Property, Lot, User, UserProperty,
    PropertyLot, TypeCrop, ConsumptionProjection, Vars
)
from app.facturation.schemas import (
    ConsumptionFilter, ConsumptionDashboardResponse,
    ConsumptionGraphData, ConsumptionListItem,
    ConsumptionManagementResponse, MyConsumptionDashboardResponse,
    PropertyConsumptionListItem, LotListItem, PropertyWithLots,
    LotDetailView, MyConsumptionResponse, ConsumptionReportRequest,
    ConsumptionReportResponse
)
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os

class ConsumptionService:
    def __init__(self, db: Session):
        self.db = db

    # Requerimiento 6: Gestión de consumo (Admin)
    def get_consumption_management(self, year: int, filters: ConsumptionFilter) -> ConsumptionManagementResponse:
        """Obtener datos de gestión de consumo para administradores"""
        try:
            # Calcular dashboard
            dashboard = self._calculate_admin_dashboard(year)
            
            # Obtener datos para la gráfica
            graph_data = self._get_consumption_graph_data(year)
            
            # Obtener lista de consumos con filtros
            consumption_list = self._get_filtered_consumption_list(filters)
            
            return ConsumptionManagementResponse(
                dashboard=dashboard,
                consumption_graph=graph_data,
                consumption_list=consumption_list
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener gestión de consumo: {str(e)}"
            )

    def _calculate_admin_dashboard(self, year: int) -> ConsumptionDashboardResponse:
        """Calcular métricas del dashboard para administradores"""
        # Consumo total del año
        total_consumption = self.db.query(
            func.sum(Consumption.registered_consumption)
        ).filter(
            extract('year', Consumption.consumption_date) == year
        ).scalar() or 0

        # Consumo promedio mensual registrado
        monthly_consumption = self.db.query(
            func.avg(Consumption.registered_consumption)
        ).filter(
            extract('year', Consumption.consumption_date) == year
        ).group_by(
            extract('month', Consumption.consumption_date)
        ).all()

        avg_monthly_consumption = sum([c[0] for c in monthly_consumption]) / len(monthly_consumption) if monthly_consumption else 0

        # Consumo promedio mensual proyectado
        monthly_projection = self.db.query(
            func.avg(ConsumptionProjection.projected_consumption)
        ).filter(
            extract('year', ConsumptionProjection.projection_date) == year
        ).group_by(
            extract('month', ConsumptionProjection.projection_date)
        ).all()

        avg_monthly_projected = sum([p[0] for p in monthly_projection]) / len(monthly_projection) if monthly_projection else 0

        # Variación esperada
        expected_variation = ((avg_monthly_projected - avg_monthly_consumption) / avg_monthly_consumption * 100) if avg_monthly_consumption else 0

        return ConsumptionDashboardResponse(
            total_consumption_m3=float(total_consumption),
            average_monthly_consumption=float(avg_monthly_consumption),
            average_monthly_projected=float(avg_monthly_projected),
            expected_variation=float(expected_variation),
            year=year
        )

    def _get_consumption_graph_data(self, year: int) -> List[ConsumptionGraphData]:
        """Obtener datos para la gráfica de consumo registrado vs proyectado"""
        months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        graph_data = []
        
        for month_num, month_name in enumerate(months, 1):
            # Consumo registrado
            registered = self.db.query(
                func.sum(Consumption.registered_consumption)
            ).filter(
                extract('year', Consumption.consumption_date) == year,
                extract('month', Consumption.consumption_date) == month_num
            ).scalar() or 0

            # Consumo proyectado
            projected = self.db.query(
                func.sum(ConsumptionProjection.projected_consumption)
            ).filter(
                extract('year', ConsumptionProjection.projection_date) == year,
                extract('month', ConsumptionProjection.projection_date) == month_num
            ).scalar() or 0

            graph_data.append(ConsumptionGraphData(
                month=month_name,
                registered_consumption=float(registered),
                projected_consumption=float(projected)
            ))
        
        return graph_data

    def _get_filtered_consumption_list(self, filters: ConsumptionFilter) -> List[ConsumptionListItem]:
        """Obtener lista de consumos con filtros aplicados"""
        query = self.db.query(
            Consumption.id,
            Property.id.label('property_id'),
            Property.name.label('property_name'),
            Lot.id.label('lot_id'),
            Lot.name.label('lot_name'),
            Lot.extension.label('extension_m2'),
            Consumption.consumption_date.label('start_date'),
            Consumption.consumption_date.label('end_date'),
            Consumption.registered_consumption.label('registered_consumption_m3')
        ).join(
            Lot, Consumption.lot_id == Lot.id
        ).join(
            PropertyLot, Lot.id == PropertyLot.lot_id
        ).join(
            Property, PropertyLot.property_id == Property.id
        )

        # Aplicar filtros
        if filters.start_date:
            query = query.filter(Consumption.consumption_date >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(Consumption.consumption_date <= filters.end_date)
        
        if filters.registered_consumption_min:
            query = query.filter(Consumption.registered_consumption >= filters.registered_consumption_min)
        
        if filters.registered_consumption_max:
            query = query.filter(Consumption.registered_consumption <= filters.registered_consumption_max)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Property.name.ilike(search_term),
                    Lot.name.ilike(search_term)
                )
            )

        results = query.all()
        
        return [
            ConsumptionListItem(
                id=r.id,
                property_id=r.property_id,
                property_name=r.property_name,
                lot_id=r.lot_id,
                lot_name=r.lot_name,
                extension_m2=r.extension_m2,
                payment_interval="Mensual",  # This should come from the database
                start_date=r.start_date,
                end_date=r.end_date,
                registered_consumption_m3=float(r.registered_consumption_m3) if r.registered_consumption_m3 else 0
            )
            for r in results
        ]

    # Requerimiento 7: Consumo de mis predios y lotes (Usuario)
    def get_my_consumption(self, user_id: int, year: int, filters: ConsumptionFilter) -> MyConsumptionResponse:
        """Obtener datos de consumo para un usuario específico"""
        try:
            # Obtener propiedades del usuario
            user_properties = self.db.query(Property).join(
                UserProperty, Property.id == UserProperty.property_id
            ).filter(UserProperty.user_id == user_id).all()

            if not user_properties:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No se encontraron propiedades para este usuario"
                )

            # Calcular dashboard
            dashboard = self._calculate_user_dashboard(user_id, year)
            
            # Obtener datos para la gráfica
            graph_data = self._get_user_consumption_graph_data(user_id, year)
            
            # Obtener lista de propiedades con consumo
            property_list = self._get_user_property_consumption_list(user_id, filters)
            
            return MyConsumptionResponse(
                dashboard=dashboard,
                consumption_graph=graph_data,
                property_list=property_list
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener consumo del usuario: {str(e)}"
            )

    def _calculate_user_dashboard(self, user_id: int, year: int) -> MyConsumptionDashboardResponse:
        """Calcular métricas del dashboard para un usuario específico"""
        # Obtener todos los lotes del usuario
        user_lots = self.db.query(Lot).join(
            PropertyLot, Lot.id == PropertyLot.lot_id
        ).join(
            Property, PropertyLot.property_id == Property.id
        ).join(
            UserProperty, Property.id == UserProperty.property_id
        ).filter(UserProperty.user_id == user_id).all()

        lot_ids = [lot.id for lot in user_lots]

        # Consumo total del año
        total_consumption = self.db.query(
            func.sum(Consumption.registered_consumption)
        ).filter(
            Consumption.lot_id.in_(lot_ids),
            extract('year', Consumption.consumption_date) == year
        ).scalar() or 0

        # Consumo promedio mensual registrado
        monthly_consumption = self.db.query(
            func.avg(Consumption.registered_consumption)
        ).filter(
            Consumption.lot_id.in_(lot_ids),
            extract('year', Consumption.consumption_date) == year
        ).group_by(
            extract('month', Consumption.consumption_date)
        ).all()

        avg_monthly_consumption = sum([c[0] for c in monthly_consumption]) / len(monthly_consumption) if monthly_consumption else 0

        # Consumo promedio mensual proyectado
        monthly_projection = self.db.query(
            func.avg(ConsumptionProjection.projected_consumption)
        ).filter(
            ConsumptionProjection.lot_id.in_(lot_ids),
            extract('year', ConsumptionProjection.projection_date) == year
        ).group_by(
            extract('month', ConsumptionProjection.projection_date)
        ).all()

        avg_monthly_projected = sum([p[0] for p in monthly_projection]) / len(monthly_projection) if monthly_projection else 0

        # Variación esperada
        expected_variation = ((avg_monthly_projected - avg_monthly_consumption) / avg_monthly_consumption * 100) if avg_monthly_consumption else 0

        return MyConsumptionDashboardResponse(
            total_consumption_m3=float(total_consumption),
            average_monthly_consumption=float(avg_monthly_consumption),
            average_monthly_projected=float(avg_monthly_projected),
            expected_variation=float(expected_variation),
            year=year
        )

    def _get_user_consumption_graph_data(self, user_id: int, year: int) -> List[ConsumptionGraphData]:
        """Obtener datos para la gráfica de consumo del usuario"""
        # Obtener todos los lotes del usuario
        user_lots = self.db.query(Lot.id).join(
            PropertyLot, Lot.id == PropertyLot.lot_id
        ).join(
            Property, PropertyLot.property_id == Property.id
        ).join(
            UserProperty, Property.id == UserProperty.property_id
        ).filter(UserProperty.user_id == user_id).all()

        lot_ids = [lot.id for lot in user_lots]

        months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        graph_data = []
        
        for month_num, month_name in enumerate(months, 1):
            # Consumo registrado
            registered = self.db.query(
                func.sum(Consumption.registered_consumption)
            ).filter(
                Consumption.lot_id.in_(lot_ids),
                extract('year', Consumption.consumption_date) == year,
                extract('month', Consumption.consumption_date) == month_num
            ).scalar() or 0

            # Consumo proyectado
            projected = self.db.query(
                func.sum(ConsumptionProjection.projected_consumption)
            ).filter(
                ConsumptionProjection.lot_id.in_(lot_ids),
                extract('year', ConsumptionProjection.projection_date) == year,
                extract('month', ConsumptionProjection.projection_date) == month_num
            ).scalar() or 0

            graph_data.append(ConsumptionGraphData(
                month=month_name,
                registered_consumption=float(registered),
                projected_consumption=float(projected)
            ))
        
        return graph_data

    def _get_user_property_consumption_list(self, user_id: int, filters: ConsumptionFilter) -> List[PropertyConsumptionListItem]:
        """Obtener lista de propiedades con consumo del usuario"""
        query = self.db.query(
            Property.id.label('property_id'),
            Property.name.label('property_name'),
            Property.extension.label('extension_m2'),
            func.min(Consumption.consumption_date).label('start_date'),
            func.max(Consumption.consumption_date).label('end_date'),
            func.sum(Consumption.registered_consumption).label('registered_consumption_m3')
        ).join(
            UserProperty, Property.id == UserProperty.property_id
        ).join(
            PropertyLot, Property.id == PropertyLot.property_id
        ).join(
            Lot, PropertyLot.lot_id == Lot.id
        ).join(
            Consumption, Lot.id == Consumption.lot_id
        ).filter(
            UserProperty.user_id == user_id
        ).group_by(
            Property.id, Property.name, Property.extension
        )

        # Aplicar filtros
        if filters.start_date:
            query = query.having(func.min(Consumption.consumption_date) >= filters.start_date)
        
        if filters.end_date:
            query = query.having(func.max(Consumption.consumption_date) <= filters.end_date)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(Property.name.ilike(search_term))

        results = query.all()
        
        return [
            PropertyConsumptionListItem(
                property_id=r.property_id,
                property_name=r.property_name,
                extension_m2=r.extension_m2,
                start_date=r.start_date,
                end_date=r.end_date,
                registered_consumption_m3=float(r.registered_consumption_m3) if r.registered_consumption_m3 else 0
            )
            for r in results
        ]

    def get_property_lots(self, property_id: int, user_id: int) -> List[LotListItem]:
        """Obtener lotes de una propiedad específica"""
        # Verificar que el usuario tiene acceso a la propiedad
        user_property = self.db.query(UserProperty).filter(
            UserProperty.user_id == user_id,
            UserProperty.property_id == property_id
        ).first()

        if not user_property:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a esta propiedad"
            )

        lots = self.db.query(
            Lot.id.label('lot_id'),
            Lot.name.label('lot_name'),
            Lot.extension.label('extension_m2'),
            TypeCrop.name.label('type_crop'),
            func.sum(Consumption.registered_consumption).label('registered_consumption_m3')
        ).join(
            PropertyLot, Lot.id == PropertyLot.lot_id
        ).join(
            TypeCrop, Lot.type_crop_id == TypeCrop.id
        ).outerjoin(
            Consumption, Lot.id == Consumption.lot_id
        ).filter(
            PropertyLot.property_id == property_id
        ).group_by(
            Lot.id, Lot.name, Lot.extension, TypeCrop.name
        ).all()

        return [
            LotListItem(
                lot_id=lot.lot_id,
                lot_name=lot.lot_name,
                extension_m2=lot.extension_m2,
                type_crop=lot.type_crop,
                registered_consumption_m3=float(lot.registered_consumption_m3) if lot.registered_consumption_m3 else 0
            )
            for lot in lots
        ]

    def get_lot_detail_consumption(self, lot_id: int, user_id: int, year: int, filters: ConsumptionFilter) -> LotDetailView:
        """Obtener detalle de consumo de un lote específico"""
        # Verificar acceso al lote
        lot = self.db.query(Lot).join(
            PropertyLot, Lot.id == PropertyLot.lot_id
        ).join(
            Property, PropertyLot.property_id == Property.id
        ).join(
            UserProperty, Property.id == UserProperty.property_id
        ).filter(
            Lot.id == lot_id,
            UserProperty.user_id == user_id
        ).first()

        if not lot:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a este lote"
            )

        # Obtener información del lote
        lot_info = self.db.query(
            Lot.id.label('lot_id'),
            Lot.name.label('lot_name'),
            Property.name.label('property_name'),
            TypeCrop.name.label('type_crop')
        ).join(
            PropertyLot, Lot.id == PropertyLot.lot_id
        ).join(
            Property, PropertyLot.property_id == Property.id
        ).join(
            TypeCrop, Lot.type_crop_id == TypeCrop.id
        ).filter(
            Lot.id == lot_id
        ).first()

        # Calcular dashboard para el lote
        dashboard = self._calculate_lot_dashboard(lot_id, year)
        
        # Obtener datos para la gráfica
        graph_data = self._get_lot_consumption_graph_data(lot_id, year)
        
        # Obtener lista de consumos del lote
        consumption_list = self._get_lot_consumption_list(lot_id, filters)

        return LotDetailView(
            lot_id=lot_info.lot_id,
            lot_name=lot_info.lot_name,
            property_name=lot_info.property_name,
            type_crop=lot_info.type_crop,
            dashboard=dashboard,
            consumption_graph=graph_data,
            consumption_list=consumption_list
        )

    def _calculate_lot_dashboard(self, lot_id: int, year: int) -> MyConsumptionDashboardResponse:
        """Calcular métricas del dashboard para un lote específico"""
        # Similar a _calculate_user_dashboard pero filtrado por un solo lote
        # (Implementación similar a los métodos anteriores)
        pass

    def _get_lot_consumption_graph_data(self, lot_id: int, year: int) -> List[ConsumptionGraphData]:
        """Obtener datos para la gráfica de consumo de un lote"""
        # Similar a _get_user_consumption_graph_data pero filtrado por un solo lote
        # (Implementación similar a los métodos anteriores)
        pass

    def _get_lot_consumption_list(self, lot_id: int, filters: ConsumptionFilter) -> List[ConsumptionListItem]:
        """Obtener lista de consumos de un lote"""
        # Similar a _get_filtered_consumption_list pero filtrado por un solo lote
        # (Implementación similar a los métodos anteriores)
        pass

    # Generación de reportes
    def generate_consumption_report(self, request: ConsumptionReportRequest, user_id: Optional[int] = None) -> ConsumptionReportResponse:
        """Generar reporte de consumo en PDF o Excel"""
        try:
            if request.format == "pdf":
                file_path = self._generate_pdf_report(request, user_id)
            else:
                file_path = self._generate_excel_report(request, user_id)

            file_name = os.path.basename(file_path)
            
            return ConsumptionReportResponse(
                file_url=f"/reports/{file_name}",
                file_name=file_name,
                generated_at=datetime.now()
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al generar reporte: {str(e)}"
            )

    def _generate_pdf_report(self, request: ConsumptionReportRequest, user_id: Optional[int] = None) -> str:
        """Generar reporte en formato PDF"""
        # Crear directorio para reportes si no existe
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"consumption_report_{timestamp}.pdf"
        filepath = os.path.join(reports_dir, filename)
        
        # Crear documento PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Título
        elements.append(Paragraph("Reporte de Consumo", title_style))
        elements.append(Spacer(1, 12))
        
        # Obtener datos según el tipo de reporte
        if request.report_type == "general":
            data = self._get_general_report_data(request.filters)
        elif request.report_type == "property" and request.property_id:
            data = self._get_property_report_data(request.property_id, request.filters)
        elif request.report_type == "lot" and request.lot_id:
            data = self._get_lot_report_data(request.lot_id, request.filters)
        else:
            raise ValueError("Tipo de reporte inválido")
        
        # Crear tabla con los datos
        table_data = [["ID", "Propiedad", "Lote", "Fecha", "Consumo (m³)"]]
        for item in data:
            table_data.append([
                str(item.id),
                item.property_name,
                item.lot_name,
                item.consumption_date.strftime("%Y-%m-%d"),
                f"{item.registered_consumption:.2f}"
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        # Generar PDF
        doc.build(elements)
        
        return filepath

    def _generate_excel_report(self, request: ConsumptionReportRequest, user_id: Optional[int] = None) -> str:
        """Generar reporte en formato Excel"""
        # Implementación similar a _generate_pdf_report pero usando pandas y openpyxl
        pass

    def _get_general_report_data(self, filters: ConsumptionFilter):
        """Obtener datos para reporte general"""
        # Implementación para obtener datos generales
        pass

    def _get_property_report_data(self, property_id: int, filters: ConsumptionFilter):
        """Obtener datos para reporte de propiedad"""
        # Implementación para obtener datos de una propiedad específica
        pass

    def _get_lot_report_data(self, lot_id: int, filters: ConsumptionFilter):
        """Obtener datos para reporte de lote"""
        # Implementación para obtener datos de un lote específico
        pass