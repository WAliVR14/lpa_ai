from fastapi import APIRouter

from app.api.v1.endpoints import nlp, reports, upload

api_router = APIRouter()

# Registro de routers por dominio / funcionalidad
api_router.include_router(
    upload.router,
    prefix="/reports",
    tags=["Ingesta y Carga de Reportes"],
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reportería y Exportación Ejecutiva"],
)

api_router.include_router(
    nlp.router,
    prefix="/nlp",
    tags=["Inteligencia Artificial y NLP"],
)
