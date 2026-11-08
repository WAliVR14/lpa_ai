import io
import openpyxl
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.lpa_models import Area, Category, Discrepancy, Report

from tests.conftest import TestingSessionLocal



def generate_excel_bytes(
    sheet_name: str = "Reporte Discrepancias LPA",
    columns: list[str] | None = None,
    rows: list[list] | None = None,
) -> bytes:
    """Genera un archivo Excel en memoria con openpyxl para pruebas de integración."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name

    default_columns = [
        "Folio",
        "Área",
        "Tema",
        "Fecha del Hallazgo",
        "Fecha Compromiso de Cierre",
        "Auditor",
        "Responsable de Cierre",
        "Descripción de la Discrepancia",
        "Solución para Cierre",
    ]
    cols = columns if columns is not None else default_columns
    ws.append(cols)

    if rows:
        for row in rows:
            ws.append(row)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# =====================================================================
# PRUEBAS DE SALUD Y RAÍZ
# =====================================================================
def test_root_and_health(client: TestClient):
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"


# =====================================================================
# PRUEBA: INGESTA EXITOSA Y VALIDACIÓN TRANSACCIONAL
# =====================================================================
def test_upload_valid_excel_success(client: TestClient):
    rows = [
        [
            "LPA-2026-001",
            "Línea de Ensamble 1",
            "EPP y Seguridad",
            "2026-08-01",
            "2026-08-11",
            "Juan Pérez",
            "Carlos López",
            "Operador sin lentes de seguridad en estación de torque.",
            "Dotación inmediata de EPP y re-entrenamiento.",
        ],
        [
            "LPA-2026-002",
            "Línea de Ensamble 1",
            "Herramientas y Calibración",
            "2026-08-02",
            "2026-08-07",
            "Ana Gómez",
            "Mario Díaz",
            "Torquímetro con etiqueta de calibración vencida por 3 días.",
            "Sustitución por equipo calibrado y envío al laboratorio.",
        ],
        [
            "LPA-2026-003",
            "Pintura y Acabados",
            "EPP y Seguridad",
            "2026-08-05",
            "2026-08-15",
            "Juan Pérez",
            "Pedro Ramírez",
            "Falta mascarilla de carbón activo en cabina de aplicación.",
            "Reposición de filtros y auditoría extraordinaria.",
        ],
    ]

    excel_data = generate_excel_bytes(rows=rows)

    response = client.post(
        "/api/v1/reports/upload",
        params={"period": "2026-Q3"},
        files={"file": ("reporte_q3.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["report_id"] == 1
    assert data["period"] == "2026-Q3"
    assert data["filename"] == "reporte_q3.xlsx"
    assert data["total_discrepancies"] == 3
    assert data["areas_registered"] == 2
    assert data["categories_registered"] == 2

    # Verificación directa en base de datos
    db = TestingSessionLocal()
    try:
        report = db.execute(select(Report).where(Report.id == 1)).scalar_one()
        assert report.total_discrepancies == 3

        areas = db.execute(select(Area)).scalars().all()
        assert len(areas) == 2
        area_names = {a.name for a in areas}
        assert area_names == {"Línea de Ensamble 1", "Pintura y Acabados"}

        categories = db.execute(select(Category)).scalars().all()
        assert len(categories) == 2
        category_names = {c.name for c in categories}
        assert category_names == {"EPP y Seguridad", "Herramientas y Calibración"}

        discrepancies = db.execute(select(Discrepancy)).scalars().all()
        assert len(discrepancies) == 3

        # Comprobar cálculo de SLA: 2026-08-11 - 2026-08-01 = 10 días
        d1 = next(d for d in discrepancies if d.folio == "LPA-2026-001")
        assert d1.closure_days_sla == 10
        assert d1.clean_description == "Operador sin lentes de seguridad en estación de torque."
        assert d1.area.name == "Línea de Ensamble 1"
        assert d1.category.name == "EPP y Seguridad"
    finally:
        db.close()


# =====================================================================
# PRUEBA: RECHAZO POR HASH DUPLICADO (HTTP 409 CONFLICT)
# =====================================================================
def test_upload_duplicate_file_conflict(client: TestClient):
    rows = [
        [
            "LPA-2026-010",
            "Almacén",
            "5S y Orden",
            "2026-08-01",
            "2026-08-03",
            "Auditor 1",
            "Responsable 1",
            "Pasillo bloqueado por tarima de producto terminado.",
            "Liberación inmediata de pasillo.",
        ]
    ]
    excel_data = generate_excel_bytes(rows=rows)

    # 1era subida: exitosa
    res1 = client.post(
        "/api/v1/reports/upload",
        params={"period": "2026-Q3"},
        files={"file": ("auditoria.xlsx", excel_data, "application/vnd.ms-excel")},
    )
    assert res1.status_code == 201

    # 2da subida: mismo archivo exacto (mismo hash SHA-256)
    res2 = client.post(
        "/api/v1/reports/upload",
        params={"period": "2026-Q3"},
        files={"file": ("auditoria_duplicada.xlsx", excel_data, "application/vnd.ms-excel")},
    )
    assert res2.status_code == 409
    assert "ya fue procesado previamente" in res2.json()["detail"]


# =====================================================================
# PRUEBA: EXTENSIÓN DE ARCHIVO INVÁLIDA (HTTP 400 BAD REQUEST)
# =====================================================================
def test_upload_invalid_extension(client: TestClient):
    response = client.post(
        "/api/v1/reports/upload",
        params={"period": "2026-Q3"},
        files={"file": ("reporte.txt", b"Texto de prueba", "text/plain")},
    )
    assert response.status_code == 400
    assert "Formato de archivo inválido" in response.json()["detail"]


# =====================================================================
# PRUEBA: HOJA DE EXCEL FALTANTE (HTTP 422 UNPROCESSABLE ENTITY)
# =====================================================================
def test_upload_missing_sheet(client: TestClient):
    excel_data = generate_excel_bytes(sheet_name="HojaErronea")

    response = client.post(
        "/api/v1/reports/upload",
        params={"period": "2026-Q3"},
        files={"file": ("reporte.xlsx", excel_data, "application/vnd.ms-excel")},
    )
    assert response.status_code == 422
    assert "Reporte Discrepancias LPA" in response.json()["detail"]


# =====================================================================
# PRUEBA: COLUMNAS REQUERIDAS FALTANTES (HTTP 422 UNPROCESSABLE ENTITY)
# =====================================================================
def test_upload_missing_required_columns(client: TestClient):
    incomplete_columns = ["Folio", "Área", "Tema"]
    excel_data = generate_excel_bytes(columns=incomplete_columns)

    response = client.post(
        "/api/v1/reports/upload",
        params={"period": "2026-Q3"},
        files={"file": ("reporte.xlsx", excel_data, "application/vnd.ms-excel")},
    )
    assert response.status_code == 422
    assert "Faltan columnas" in response.json()["detail"]


# =====================================================================
# PRUEBA: FORMATO DE PERIODO INVÁLIDO (HTTP 422)
# =====================================================================
def test_upload_invalid_period_format(client: TestClient):
    excel_data = generate_excel_bytes()

    response = client.post(
        "/api/v1/reports/upload",
        params={"period": "2026-Q5"},  # Q5 no es válido en el regex ^\d{4}-Q[1-4]$
        files={"file": ("reporte.xlsx", excel_data, "application/vnd.ms-excel")},
    )
    assert response.status_code == 422


# =====================================================================
# PRUEBA: REUTILIZACIÓN DE CATÁLOGOS (UPSERT MULTI-REPORTE)
# =====================================================================
def test_catalog_upsert_reutilization(client: TestClient):
    # Reporte 1 con Área A y Área B
    r1 = generate_excel_bytes(
        rows=[
            ["F1", "Área Alpha", "Tema 1", "2026-07-01", "2026-07-05", "Auditor", "Resp", "D1", "S1"],
            ["F2", "Área Beta", "Tema 1", "2026-07-01", "2026-07-05", "Auditor", "Resp", "D2", "S2"],
        ]
    )
    res1 = client.post(
        "/api/v1/reports/upload",
        params={"period": "2026-Q3"},
        files={"file": ("r1.xlsx", r1, "application/vnd.ms-excel")},
    )
    assert res1.status_code == 201

    # Reporte 2 con Área Alpha (existente) y Área Gamma (nueva)
    r2 = generate_excel_bytes(
        rows=[
            ["F3", "Área Alpha", "Tema 2", "2026-07-10", "2026-07-15", "Auditor", "Resp", "D3", "S3"],
            ["F4", "Área Gamma", "Tema 1", "2026-07-10", "2026-07-15", "Auditor", "Resp", "D4", "S4"],
        ]
    )
    res2 = client.post(
        "/api/v1/reports/upload",
        params={"period": "2026-Q3"},
        files={"file": ("r2.xlsx", r2, "application/vnd.ms-excel")},
    )
    assert res2.status_code == 201

    db = TestingSessionLocal()
    try:
        areas = db.execute(select(Area)).scalars().all()
        # Debe haber exactamente 3 áreas: Alpha, Beta, Gamma (sin duplicar Alpha)
        assert len(areas) == 3
        assert {a.name for a in areas} == {"Área Alpha", "Área Beta", "Área Gamma"}

        categories = db.execute(select(Category)).scalars().all()
        # Debe haber exactamente 2 categorías: Tema 1 y Tema 2 (sin duplicar Tema 1)
        assert len(categories) == 2
        assert {c.name for c in categories} == {"Tema 1", "Tema 2"}
    finally:
        db.close()

