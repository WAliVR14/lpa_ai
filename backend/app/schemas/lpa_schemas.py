from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class DiscrepancyRaw(BaseModel):
    """
    Esquema Pydantic de transición.
    Garantiza que la fila del Excel tenga los tipos de datos correctos
    antes de ser convertida a un modelo de SQLAlchemy.
    """
    folio: str
    area: str
    category: str
    finding_date: date
    commitment_date: date
    auditor: str
    responsible: str
    raw_description: str
    closure_solution: str

    model_config = ConfigDict(from_attributes=True)


class UploadResponse(BaseModel):
    """
    Respuesta estructurada tras la ingesta exitosa de un archivo Excel de discrepancias LPA.
    """
    report_id: int
    period: str
    filename: str
    file_hash: str
    total_discrepancies: int
    areas_registered: int
    categories_registered: int
    uploaded_at: datetime
    message: str = "Reporte LPA procesado e insertado exitosamente."

    model_config = ConfigDict(from_attributes=True)


class TopOffenderSummary(BaseModel):
    """
    Resumen de un Top Offender (clúster semántico) detectado.
    """
    id: int
    rank_position: int
    category_id: int
    category_name: str
    canonical_description: str
    occurrence_count: int
    percentage_of_total: float

    model_config = ConfigDict(from_attributes=True)


class ClusterReportResponse(BaseModel):
    """
    Respuesta tras la ejecución del motor de agrupamiento semántico NLP.
    """
    report_id: int
    period: str
    total_discrepancies: int
    total_clusters: int
    top_offenders: list[TopOffenderSummary]
    message: str

    model_config = ConfigDict(from_attributes=True)
