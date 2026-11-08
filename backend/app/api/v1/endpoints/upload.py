import hashlib
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.lpa_models import Area, Category, Discrepancy, Report
from app.schemas.lpa_schemas import UploadResponse
from app.services.etl_service import ETLService

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingesta de Reporte Excel LPA",
    description="Recibe un archivo Excel con discrepancias LPA, valida su formato mediante ETLService, "
                "calcula el hash SHA-256 para evitar duplicados y persiste transaccionalmente "
                "el reporte, catálogos (Area, Category) y discrepancias asociadas.",
)
async def upload_lpa_report(
    file: UploadFile = File(..., description="Archivo Excel (.xlsx o .xls) exportado de LPA"),
    period: str = Query(
        ...,
        description="Periodo trimestral del reporte (formato AAAA-QT, ej. '2026-Q3')",
        pattern=r"^\d{4}-Q[1-4]$",
        examples=["2026-Q3"],
    ),
    db: Session = Depends(get_db),
) -> UploadResponse:
    # 1. Validación de extensión de archivo
    filename = file.filename or "reporte.xlsx"
    if not (filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo inválido. Se requiere un archivo Excel con extensión .xlsx o .xls",
        )

    # 2. Guardar en disco temporal y calcular hash SHA-256 en streaming
    sha256_hash = hashlib.sha256()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    temp_path = Path(temp_file.name)

    try:
        try:
            while chunk := await file.read(64 * 1024):  # Chunks de 64 KB
                sha256_hash.update(chunk)
                temp_file.write(chunk)
            temp_file.flush()
        finally:
            temp_file.close()

        file_hash = sha256_hash.hexdigest()

        # 3. Verificación de duplicados por hash SHA-256 (HTTP 409 Conflict)
        existing_report = db.execute(
            select(Report).where(Report.file_hash == file_hash)
        ).scalar_one_or_none()

        if existing_report:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"El archivo '{filename}' ya fue procesado previamente con ID #{existing_report.id} "
                    f"en el periodo '{existing_report.period}' el {existing_report.uploaded_at.isoformat()}."
                ),
            )

        # 4. Procesamiento y validación ETL (Fail-Fast)
        try:
            cleaned_records = ETLService.process_excel(temp_path)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Error en validación del archivo Excel: {str(exc)}",
            )

        if not cleaned_records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo Excel no contiene discrepancias válidas para procesar.",
            )

        # 5. Persistencia Transaccional Atómica
        try:
            # 5.1 Registro principal de Reporte
            new_report = Report(
                period=period,
                filename=filename,
                file_hash=file_hash,
                total_discrepancies=len(cleaned_records),
            )
            db.add(new_report)
            db.flush()  # Asigna el ID autoincremental de new_report

            # 5.2 Upsert en memoria de catálogos Area y Category
            existing_areas: dict[str, Area] = {
                a.name: a for a in db.execute(select(Area)).scalars().all()
            }
            existing_categories: dict[str, Category] = {
                c.name: c for c in db.execute(select(Category)).scalars().all()
            }

            for record in cleaned_records:
                area_name = record.area.strip()
                if area_name not in existing_areas:
                    new_area = Area(name=area_name)
                    db.add(new_area)
                    existing_areas[area_name] = new_area

                category_name = record.category.strip()
                if category_name not in existing_categories:
                    new_cat = Category(name=category_name)
                    db.add(new_cat)
                    existing_categories[category_name] = new_cat

            db.flush()  # Genera IDs para las nuevas áreas y categorías

            # 5.3 Inserción de filas en Discrepancy
            for record in cleaned_records:
                sla_days = (record.commitment_date - record.finding_date).days
                area_obj = existing_areas[record.area.strip()]
                category_obj = existing_categories[record.category.strip()]

                discrepancy = Discrepancy(
                    report_id=new_report.id,
                    area_id=area_obj.id,
                    category_id=category_obj.id,
                    top_offender_id=None,
                    folio=record.folio.strip(),
                    finding_date=record.finding_date,
                    commitment_date=record.commitment_date,
                    closure_days_sla=sla_days,
                    auditor=record.auditor.strip(),
                    responsible=record.responsible.strip(),
                    raw_description=record.raw_description.strip(),
                    clean_description=record.raw_description.strip(),
                    closure_solution=record.closure_solution.strip(),
                    embedding_json=None,
                )
                db.add(discrepancy)

            # 5.4 Commit final solo si todos los registros pasaron sin error
            db.commit()
            db.refresh(new_report)

            return UploadResponse(
                report_id=new_report.id,
                period=new_report.period,
                filename=new_report.filename,
                file_hash=new_report.file_hash,
                total_discrepancies=new_report.total_discrepancies,
                areas_registered=len(existing_areas),
                categories_registered=len(existing_categories),
                uploaded_at=new_report.uploaded_at,
                message=f"Reporte '{new_report.filename}' ({new_report.period}) procesado exitosamente con {new_report.total_discrepancies} discrepancias.",
            )

        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Conflicto de integridad en base de datos (posible folio duplicado): {str(exc.orig or exc)}",
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Fallo durante la persistencia transaccional: {str(exc)}",
            )

    finally:
        # 6. Limpieza garantizada del archivo temporal en disco
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

