import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.lpa_models import Area, Category, Discrepancy, Report, TopOffender

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_cluster_report_not_found(client: TestClient):
    response = client.post("/api/v1/nlp/cluster/9999")
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"]


def test_cluster_report_empty_discrepancies(client: TestClient):
    db = TestingSessionLocal()
    report = Report(
        period="2026-Q3",
        filename="empty.xlsx",
        file_hash="hash_empty_123",
        total_discrepancies=0,
    )
    db.add(report)
    db.commit()
    report_id = report.id
    db.close()

    response = client.post(f"/api/v1/nlp/cluster/{report_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_discrepancies"] == 0
    assert data["total_clusters"] == 0
    assert len(data["top_offenders"]) == 0


def test_cluster_semantic_grouping_and_reprocessing(client: TestClient):
    db = TestingSessionLocal()

    # 1. Crear datos iniciales
    report = Report(
        period="2026-Q3",
        filename="auditoria_seguridad.xlsx",
        file_hash="hash_seguridad_abc",
        total_discrepancies=4,
    )
    db.add(report)

    area = Area(name="Línea de Ensamble")
    cat_seguridad = Category(name="EPP y Seguridad")
    cat_calidad = Category(name="Calidad y Torques")
    db.add_all([area, cat_seguridad, cat_calidad])
    db.flush()

    # 3 discrepancias semánticamente muy similares en Seguridad
    d1 = Discrepancy(
        report_id=report.id,
        area_id=area.id,
        category_id=cat_seguridad.id,
        folio="FOL-001",
        finding_date=date(2026, 8, 1),
        commitment_date=date(2026, 8, 10),
        closure_days_sla=9,
        auditor="Auditor A",
        responsible="Líder A",
        raw_description="Operador no porta lentes de protección en estación de ensamble.",
        clean_description="Operador no porta lentes de protección en estación de ensamble.",
        closure_solution="Entrega de EPP.",
    )
    d2 = Discrepancy(
        report_id=report.id,
        area_id=area.id,
        category_id=cat_seguridad.id,
        folio="FOL-002",
        finding_date=date(2026, 8, 2),
        commitment_date=date(2026, 8, 12),
        closure_days_sla=10,
        auditor="Auditor B",
        responsible="Líder A",
        raw_description="Operador trabajando sin gafas de seguridad obligatorias.",
        clean_description="Operador trabajando sin gafas de seguridad obligatorias.",
        closure_solution="Entrega de gafas.",
    )
    d3 = Discrepancy(
        report_id=report.id,
        area_id=area.id,
        category_id=cat_seguridad.id,
        folio="FOL-003",
        finding_date=date(2026, 8, 3),
        commitment_date=date(2026, 8, 13),
        closure_days_sla=10,
        auditor="Auditor C",
        responsible="Líder A",
        raw_description="Falta de uso de lentes de protección personal en línea.",
        clean_description="Falta de uso de lentes de protección personal en línea.",
        closure_solution="Plática de concientización.",
    )
    # 1 discrepancia en otra categoría (Calidad)
    d4 = Discrepancy(
        report_id=report.id,
        area_id=area.id,
        category_id=cat_calidad.id,
        folio="FOL-004",
        finding_date=date(2026, 8, 4),
        commitment_date=date(2026, 8, 14),
        closure_days_sla=10,
        auditor="Auditor D",
        responsible="Líder B",
        raw_description="Torquímetro digital fuera de calibración.",
        clean_description="Torquímetro digital fuera de calibración.",
        closure_solution="Calibrar equipo.",
    )

    db.add_all([d1, d2, d3, d4])
    db.commit()
    report_id = report.id
    db.close()

    # 2. Ejecutar endpoint de NLP
    response = client.post(f"/api/v1/nlp/cluster/{report_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["report_id"] == report_id
    assert data["total_discrepancies"] == 4
    assert data["total_clusters"] == 2  # 1 clúster de lentes (3) + 1 clúster de torquímetro (1)

    top_offenders = data["top_offenders"]
    assert len(top_offenders) == 2

    # El Top Offender de mayor ocurrencia debe ser el Rank 1 (los 3 de lentes de seguridad)
    top1 = top_offenders[0]
    assert top1["rank_position"] == 1
    assert top1["occurrence_count"] == 3
    assert top1["percentage_of_total"] == 75.0
    assert top1["category_name"] == "EPP y Seguridad"

    top2 = top_offenders[1]
    assert top2["rank_position"] == 2
    assert top2["occurrence_count"] == 1
    assert top2["percentage_of_total"] == 25.0
    assert top2["category_name"] == "Calidad y Torques"

    # 3. Verificar persistencia en base de datos
    db = TestingSessionLocal()
    try:
        db_offenders = db.execute(select(TopOffender).where(TopOffender.report_id == report_id)).scalars().all()
        assert len(db_offenders) == 2

        db_discrepancies = db.execute(select(Discrepancy).where(Discrepancy.report_id == report_id)).scalars().all()
        # Todas las discrepancias deben tener un top_offender_id asignado y embedding_json
        for d in db_discrepancies:
            assert d.top_offender_id is not None
            assert d.embedding_json is not None
            assert len(d.embedding_json) > 10

        # Verificar que el cluster 1 tiene asociadas exactamente 3 discrepancias
        offender_1_discrepancies = [d for d in db_discrepancies if d.top_offender_id == top1["id"]]
        assert len(offender_1_discrepancies) == 3
    finally:
        db.close()

    # 4. Probar idempotencia y reprocesamiento
    # Al llamar de nuevo el endpoint no debe fallar ni duplicar registros
    response_retry = client.post(f"/api/v1/nlp/cluster/{report_id}")
    assert response_retry.status_code == 200
    data_retry = response_retry.json()
    assert data_retry["total_clusters"] == 2

