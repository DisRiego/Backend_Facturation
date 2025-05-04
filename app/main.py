from fastapi import FastAPI
from app.database import Base, engine
from app.facturation.routes import router as facturation_router
from app.middlewares import setup_middlewares
from app.exceptions import setup_exception_handlers

# **Configurar FastAPI**
app = FastAPI( 
    title="Distrito de Riego API Gateway - Facturación y Consumo",
    description="API Gateway para Facturación y Consumo en el sistema de riego",
    version="1.0.0"
)

# **Configurar Middlewares**
setup_middlewares(app)

# **Configurar Manejadores de Excepciones**
setup_exception_handlers(app)

# **Registrar Rutas**
app.include_router(facturation_router)

Base.metadata.create_all(bind=engine)

# **Endpoint de Salud**
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}