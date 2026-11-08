import io
import pytest
from datetime import date
from fastapi.testclient import TestClient
from pptx import Presentation
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.lpa_models import Area, Category, Discrepancy, Report, TopOffender

from tests.conftest import TestingSessionLocal



def test_download_report_not_found(client: TestClient):
    response = client.get("/api/v1/reports/download/9999")
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"]


def test_download_report_without_top_offenders(client: TestClient):
    db = TestingSessionLocal()
    report = Report(
        period="2026-Q3",
        filename="reporte_sin_top.xlsx",
        file_hash="hash_no_top_999",
        total_discrepancies=5,
    )
    db.add(report)
    db.commit()
    report_id = report.id
    db.close()

    response = client.get(f"/api/v1/reports/download/{report_id}")
    assert response.status_code == 404
    assert "no contiene Top Offenders" in response.json()["detail"]


def test_generate_and_download_pptx_success(client: TestClient):
    db = TestingSessionLocal()

    # 1. Crear Reporte
    report = Report(
        period="2026-Q3",
        filename="auditoria_q3.xlsx",
        file_hash="hash_test_pptx_123",
        total_discrepancies=15,
    )
    db.add(report)

    # 2. Crear Áreas y Categorías
    area = Area(name="Línea de Ensamble")
    cat1 = Category(name="EPP y Seguridad")
    cat2 = Category(name="Calidad y Torques")
    cat3 = Category(name="5S y Limpieza")
    db.add_all([area, cat1, cat2, cat3])
    db.flush()

    # 3. Crear 5 Top Offenders
    offenders_data = [
        (1, cat1.id, "Operador sin lentes de seguridad en estación de torque.", 5, 33.3),
        (2, cat2.id, "Torquímetro digital con calibración vencida.", 4, 26.7),
        (3, cat3.id, "Pasillos de tránsito obstruidos por tarimas.", 3, 20.0),
        (4, cat1.id, "Falta de tapones auditivos en área de prensa.", 2, 13.3),
        (5, cat2.id, "Perno de fijación sin marca de torque verificado.", 1, 6.7),
    ]

    for rank, cat_id, desc, count, pct in offenders_data:
        to = TopOffender(
            report_id=report.id,
            category_id=cat_id,
            canonical_description=desc,
            occurrence_count=count,
            percentage_of_total=pct,
            rank_position=rank,
        )
        db.add(to)

    # 4. Crear discrepancias asociadas a las categorías para el gráfico de pastel
    for i in range(15):
        c_id = cat1.id if i < 7 else (cat2.id if i < 12 else cat3.id)
        d = Discrepancy(
            report_id=report.id,
            area_id=area.id,
            category_id=c_id,
            folio=f"FOL-PPTX-{i:03d}",
            finding_date=date(2026, 8, 1),
            commitment_date=date(2026, 8, 10),
            closure_days_sla=9,
            auditor="Auditor Prueba",
            responsible="Líder Prueba",
            raw_description=f"Descripción de prueba {i}",
            clean_description=f"Descripción limpia {i}",
            closure_solution="Solución de prueba",
        )
        db.add(d)

    db.commit()
    report_id = report.id
    db.close()

    # 5. Ejecutar la descarga del archivo PPTX
    response = client.get(f"/api/v1/reports/download/{report_id}")
    assert response.status_code == 200

    # Verificar Content-Type y cabecera de descarga
    assert "application/vnd.openxmlformats-officedocument.presentationml.presentation" in response.headers["content-type"]
    assert "Reporte_Ejecutivo_LPA_2026-Q3.pptx" in response.headers["content-disposition"]

    # 6. Validar que los bytes recibidos correspondan a un PowerPoint válido
    pptx_bytes = io.BytesIO(response.content)
    prs = Presentation(pptx_bytes)

    # Debe contener 7 diapositivas: 1 Portada + 1 Resumen + 5 Top Offenders
    assert len(prs.slides) == 7

    # Slide 1: Portada
    slide_cover = prs.slides[0]
    cover_text = " ".join(shape.text_frame.text for shape in slide_cover.shapes if shape.has_text_frame)
    assert "Resumen Trimestral LPA - 2026-Q3" in cover_text
    assert "Aumovio" in cover_text

    # Slide 2: Resumen
    slide_summary = prs.slides[1]
    summary_text = " ".join(shape.text_frame.text for shape in slide_summary.shapes if shape.has_text_frame)
    assert "Resumen Ejecutivo de Auditorías LPA" in summary_text
    assert "15" in summary_text  # Total de discrepancias

    # Slide 3: Top Offender #1
    slide_to1 = prs.slides[2]
    to1_text = " ".join(shape.text_frame.text for shape in slide_to1.shapes if shape.has_text_frame)
    assert "Top Offender #1: EPP y Seguridad" in to1_text
    assert "Operador sin lentes de seguridad" in to1_text

