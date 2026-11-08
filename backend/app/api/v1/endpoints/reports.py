from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path as PathParam, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.lpa_models import Report
from app.services.report_service import ReportService

router = APIRouter()


def remove_temp_file(file_path: str):
    """Tarea en segundo plano para limpiar el archivo .pptx temporal una vez enviado al cliente."""
    try:
        p = Path(file_path)
        if p.exists():
            p.unlink()
    except Exception:
        pass


@router.get(
    "/download/{report_id}",
    summary="Descargar Reporte Ejecutivo en PowerPoint (.pptx)",
    description=(
        "Genera dinámicamente y descarga la presentación ejecutiva en PowerPoint de los Top Offenders "
        "de un reporte LPA, incluyendo portada, resumen de auditorías, gráfica de pastel y detalle de los Top 5 problemas."
    ),
    response_class=FileResponse,
)
def download_executive_report(
    background_tasks: BackgroundTasks,
    report_id: int = PathParam(..., description="ID del reporte LPA a exportar", ge=1),
    db: Session = Depends(get_db),
):
    # 1. Obtener periodo para el nombre del archivo descargable
    report = db.execute(select(Report).where(Report.id == report_id)).scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reporte con ID #{report_id} no encontrado en la base de datos.",
        )

    # 2. Generar presentación mediante ReportService
    try:
        file_path = ReportService.generate_pptx_report(db=db, report_id=report_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al construir la presentación PowerPoint: {str(exc)}",
        )

    # 3. Registrar eliminación del archivo temporal tras el envío
    background_tasks.add_task(remove_temp_file, file_path)

    # 4. Retornar archivo físico con cabeceras MIME adecuadas
    download_filename = f"Reporte_Ejecutivo_LPA_{report.period}.pptx"
    return FileResponse(
        path=file_path,
        filename=download_filename,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )

