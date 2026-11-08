from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor del ciclo de vida de la aplicación.
    Inicializa las tablas en la base de datos al arrancar y libera recursos al apagar.
    """
    # Startup: Crear tablas si no existen (SQLite local o PostgreSQL)
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown


# Inicialización de FastAPI con metadatos oficiales de Aumovio
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Sistema integral de Inteligencia Artificial y Procesamiento de Datos para la ingesta, "
        "limpieza, normalización y análisis de reportes de Auditorías de Procesos por Capas (LPA)."
    ),
    lifespan=lifespan,
)

# Configuración de CORS para permitir la conexión desde el frontend (React + Vite)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*",  # Permite desarrollo local y pruebas desde cualquier origen
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión del enrutador principal de la API v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Estado"])
def root():
    """Ruta raíz de bienvenida e inspección rápida."""
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/health", tags=["Estado"])
def health_check():
    """Sonda de salud para orquestadores y monitoreo."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
    }

