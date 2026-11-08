# Sistema de IA para Análisis de Discrepancias LPA y Detección de Top Offenders — Aumovio

Sistema integral de Ingeniería de Datos, Inteligencia Artificial (NLP) y Visualización diseñado para automatizar el procesamiento de reportes de **Auditorías de Procesos por Capas (LPA)** en formato Excel, identificar patrones semánticos recurrentes (*Top Offenders*) mediante el cálculo de Medoides, y generar reportes ejecutivos trimestrales en PowerPoint (.pptx).

---

## 🏗 Arquitectura del Sistema

- **Backend:** Python 3.11 + FastAPI + SQLAlchemy 2.0 (ORM) + Pydantic v2
- **Motor ETL & Estadístico:** Pandas + NumPy + OpenPyXL
- **Motor de Inteligencia Artificial (NLP):**
  - Modelo: `paraphrase-multilingual-MiniLM-L12-v2` (Hugging Face / Sentence-Transformers)
  - Algoritmo: Clustering Jerárquico Aglomerativo (`metric='cosine'`, `distance_threshold=0.22`)
  - Medoide: Punto de menor distancia coseno promedio en cada clúster semántico
- **Reportería Ejecutiva:** `python-pptx` + `matplotlib` (renderizado headless en memoria con backend Agg)
- **Frontend SPA:** React 18 + Vite 6 + Tailwind CSS + Lucide Icons + Recharts
- **Infraestructura & Despliegue:** Docker, Docker Compose y Nginx Reverse Proxy

---

## 🚀 Despliegue con Docker Compose

El proyecto está 100% contenedorizado para un despliegue reproducible con un solo comando:

```bash
docker compose up --build -d
```

### Servicios Desplegados:
| Servicio | Tecnología | Puerto Local | Descripción |
| :--- | :--- | :--- | :--- |
| **Frontend** | Nginx Alpine + React SPA | `http://localhost:80` | Panel de Control e Interfaz de Usuario |
| **Backend** | FastAPI + Uvicorn | `http://localhost:8000` | API REST y Motor de Inferencia NLP |
| **Documentación** | Swagger UI interactivo | `http://localhost:8000/docs` | OpenAPI Specification |

Para detener los servicios:
```bash
docker compose down
```

Para visualizar los registros en tiempo real:
```bash
docker compose logs -f
```

---

## 🌐 Endpoints Principales de la API (v1)

### 1. Ingesta de Reporte Excel
- **POST** `/api/v1/reports/upload?period={period}`
  - Recibe: Multipart form-data (`file: .xlsx`) y query param `period` (ej. `2026-Q3`).
  - Lógica: Calcula hash SHA-256 (rechaza duplicados con `409 Conflict`), valida estructura con `ETLService`, realiza upsert de catálogos (`Area`, `Category`) e inserta discrepancias con rollback atómico.

### 2. Agrupamiento Semántico y NLP
- **POST** `/api/v1/nlp/cluster/{report_id}`
  - Recibe: `report_id` (entero).
  - Lógica: Genera embeddings densos con `MiniLM-L12`, agrupa discrepancias por categoría, calcula el medoide canónico de cada clúster, asigna rankings y persiste los `TopOffender`.

### 3. Descarga de Presentación Ejecutiva
- **GET** `/api/v1/reports/download/{report_id}`
  - Recibe: `report_id` (entero).
  - Lógica: Genera una presentación PowerPoint (.pptx) de 7 diapositivas con portada corporativa, resumen con gráfica de pastel (`matplotlib`) y diapositivas individuales para los Top 5 problemas con limpieza automática de archivos temporales.

---

## 🧪 Ejecución de Pruebas Automatizadas

Para correr la suite de pruebas unitarias y de integración del backend:

```bash
# Activar entorno virtual
.venv/bin/activate  # En Linux/Mac
.venv\Scripts\Activate.ps1  # En Windows

# Ejecutar pytest con conftest unificado
pytest backend/tests/ -v
```

---

## 📁 Estructura del Monorepo

```
lpa_ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── upload.py      # Ingesta y deduplicación SHA-256
│   │   │   │   ├── nlp.py         # Clustering y Top Offenders
│   │   │   │   └── reports.py     # Generación de PPTX
│   │   │   └── api.py             # Agrupador de rutas v1
│   │   ├── core/
│   │   │   ├── config.py          # Variables de entorno
│   │   │   └── database.py        # Motor SQLAlchemy y sesiones
│   │   ├── models/
│   │   │   └── lpa_models.py      # Modelos ORM relacionales
│   │   ├── schemas/
│   │   │   └── lpa_schemas.py     # Esquemas de validación Pydantic v2
│   │   ├── services/
│   │   │   ├── etl_service.py     # Validación y limpieza de Excel
│   │   │   ├── nlp_service.py     # Embeddings y cálculo de Medoide
│   │   │   └── report_service.py  # Generador de diapositivas PPTX
│   │   └── main.py                # Aplicación FastAPI y CORS
│   ├── tests/
│   │   ├── conftest.py            # Fixtures de BD aislada en memoria
│   │   ├── test_upload.py         # Pruebas de ingesta y validaciones
│   │   ├── test_nlp.py            # Pruebas de agrupamiento semántico
│   │   └── test_reports.py        # Pruebas de exportación PPTX
│   ├── Dockerfile                 # Contenedor Python 3.11-slim
│   ├── .dockerignore
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.jsx         # Sidebar y Header corporativo
│   │   │   ├── UploadSection.jsx  # Drag & drop y selector de periodo
│   │   │   ├── DashboardCards.jsx # KPIs en tiempo real
│   │   │   └── TopOffendersTable.jsx # Tabla y gráficos Recharts
│   │   ├── services/
│   │   │   └── api.js             # Cliente Axios hacia FastAPI
│   │   ├── App.jsx                # Orquestador del flujo operativo
│   │   └── main.jsx
│   ├── nginx.conf                 # Configuración de Nginx SPA y proxy
│   ├── Dockerfile                 # Multi-stage build (Node 20 + Nginx)
│   ├── .dockerignore
│   ├── package.json
│   └── tailwind.config.js
├── docker-compose.yml             # Orquestación de servicios
├── Makefile                       # Comandos abreviados de desarrollo
└── README.md
```
