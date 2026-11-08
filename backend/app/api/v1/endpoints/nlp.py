from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.lpa_schemas import ClusterReportResponse
from app.services.nlp_service import NLPService

router = APIRouter()


@router.post(
    "/cluster/{report_id}",
    response_model=ClusterReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Agrupamiento Semántico y Detección de Top Offenders",
    description=(
        "Ejecuta el pipeline de Machine Learning y Procesamiento de Lenguaje Natural (NLP) sobre "
        "las discrepancias del reporte especificado. Agrupa semánticamente por categoría, "
        "determina los 'Top Offenders' mediante el cálculo del Medoide y persiste las relaciones."
    ),
)
def cluster_report(
    report_id: int = Path(..., description="Identificador único del reporte LPA", ge=1),
    db: Session = Depends(get_db),
) -> ClusterReportResponse:
    try:
        result = NLPService.cluster_report_discrepancies(db=db, report_id=report_id)
        return ClusterReportResponse(**result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo durante la ejecución del pipeline NLP: {str(exc)}",
        )

