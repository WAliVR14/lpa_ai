import json
from typing import Any
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, joinedload

from app.models.lpa_models import Discrepancy, Report, TopOffender


class NLPService:
    """
    Servicio de Inteligencia Artificial y Machine Learning para procesamiento de lenguaje natural (NLP).
    Agrupa semánticamente las discrepancias de un reporte LPA para detectar clústeres ('Top Offenders')
    utilizando embeddings multilingües, clustering aglomerativo y cálculo del Medoide representativo.
    """

    _model: Any = None
    _model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"

    @classmethod
    def get_model(cls) -> Any:
        """
        Carga el modelo SentenceTransformer de HuggingFace como Singleton en memoria
        para optimizar la latencia y evitar recargar los pesos en cada petición.
        """
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(cls._model_name)
        return cls._model

    @classmethod
    def cluster_report_discrepancies(cls, db: Session, report_id: int) -> dict[str, Any]:
        """
        Ejecuta el pipeline completo de NLP sobre las discrepancias de un reporte:
        1. Limpieza de Top Offenders previos (soporte de reprocesamiento idempotente).
        2. Agrupación por categoría temática (category_id).
        3. Generación de embeddings densos con el modelo de lenguaje multilingüe.
        4. Agrupamiento jerárquico aglomerativo (cosine distance <= 0.22).
        5. Identificación del Medoide canónico para cada clúster.
        6. Asignación de ranking por frecuencia, porcentajes y persistencia atómica.
        """
        # 1. Validar existencia del reporte
        report = db.execute(select(Report).where(Report.id == report_id)).scalar_one_or_none()
        if not report:
            raise ValueError(f"Reporte con ID #{report_id} no encontrado.")

        # 2. Desvincular top_offenders previos y eliminarlos para permitir reprocesamiento
        db.execute(
            update(Discrepancy)
            .where(Discrepancy.report_id == report_id)
            .values(top_offender_id=None)
        )
        db.execute(
            delete(TopOffender).where(TopOffender.report_id == report_id)
        )
        db.flush()

        # 3. Extraer todas las discrepancias del reporte
        discrepancies = db.execute(
            select(Discrepancy)
            .options(joinedload(Discrepancy.category))
            .where(Discrepancy.report_id == report_id)
        ).scalars().all()

        total_discrepancies = len(discrepancies)
        if total_discrepancies == 0:
            db.commit()
            return {
                "report_id": report.id,
                "period": report.period,
                "total_discrepancies": 0,
                "total_clusters": 0,
                "top_offenders": [],
                "message": f"El reporte #{report_id} no cuenta con discrepancias registradas para agrupar.",
            }

        # 4. Agrupar discrepancias por category_id
        discrepancies_by_cat: dict[int, list[Discrepancy]] = {}
        category_names: dict[int, str] = {}
        for d in discrepancies:
            discrepancies_by_cat.setdefault(d.category_id, []).append(d)
            if d.category and d.category_id not in category_names:
                category_names[d.category_id] = d.category.name

        # 5. Inicializar modelo de lenguaje y estructuras de clústeres
        model = cls.get_model()
        created_offenders: list[tuple[TopOffender, list[Discrepancy]]] = []

        for category_id, cat_discrepancies in discrepancies_by_cat.items():
            texts = [
                d.clean_description.strip() if d.clean_description else d.raw_description.strip()
                for d in cat_discrepancies
            ]

            # 5.1 Generar embeddings normalizados
            embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

            # Guardar embedding serializado en cada Discrepancy
            for d, emb in zip(cat_discrepancies, embeddings):
                d.embedding_json = json.dumps(emb.tolist())

            # 5.2 Si hay 1 solo hallazgo en la categoría: crear TopOffender unitario
            if len(cat_discrepancies) == 1:
                single_d = cat_discrepancies[0]
                offender = TopOffender(
                    report_id=report_id,
                    category_id=category_id,
                    canonical_description=single_d.clean_description or single_d.raw_description,
                    occurrence_count=1,
                    percentage_of_total=0.0,
                    rank_position=0,
                    centroid_embedding_json=json.dumps(embeddings[0].tolist()),
                )
                created_offenders.append((offender, [single_d]))

            else:
                # 5.3 Agrupamiento jerárquico aglomerativo
                clustering = AgglomerativeClustering(
                    metric="cosine",
                    linkage="average",
                    distance_threshold=0.22,
                    n_clusters=None,
                )
                labels = clustering.fit_predict(embeddings)

                # Organizar miembros por etiqueta de clúster
                clusters_dict: dict[int, list[int]] = {}
                for idx, label in enumerate(labels):
                    clusters_dict.setdefault(int(label), []).append(idx)

                for _, member_indices in clusters_dict.items():
                    member_discrepancies = [cat_discrepancies[i] for i in member_indices]
                    member_embeddings = embeddings[member_indices]

                    if len(member_indices) == 1:
                        medoid_d = member_discrepancies[0]
                        centroid_vec = member_embeddings[0]
                    else:
                        # Cálculo del Medoide: punto con menor distancia coseno promedio hacia los demás del clúster
                        dist_matrix = cosine_distances(member_embeddings, member_embeddings)
                        mean_distances = dist_matrix.mean(axis=1)
                        medoid_sub_idx = int(np.argmin(mean_distances))
                        medoid_d = member_discrepancies[medoid_sub_idx]
                        centroid_vec = member_embeddings.mean(axis=0)

                    offender = TopOffender(
                        report_id=report_id,
                        category_id=category_id,
                        canonical_description=medoid_d.clean_description or medoid_d.raw_description,
                        occurrence_count=len(member_indices),
                        percentage_of_total=0.0,
                        rank_position=0,
                        centroid_embedding_json=json.dumps(centroid_vec.tolist()),
                    )
                    created_offenders.append((offender, member_discrepancies))

        # 6. Asignar Ranking y Porcentajes Globales del Reporte
        # Ordenar por ocurrencias descendente (y alfabéticamente por descripción como criterio de desempate)
        created_offenders.sort(key=lambda item: (-item[0].occurrence_count, item[0].canonical_description))

        for rank, (offender, _) in enumerate(created_offenders, start=1):
            offender.rank_position = rank
            offender.percentage_of_total = round((offender.occurrence_count / total_discrepancies) * 100, 2)
            db.add(offender)

        db.flush()  # Genera IDs para los TopOffenders creados

        # 7. Asociar las llaves foráneas top_offender_id en las Discrepancies correspondientes
        for offender, member_discrepancies in created_offenders:
            for d in member_discrepancies:
                d.top_offender_id = offender.id

        # 8. Persistencia transaccional garantizada
        db.commit()

        # 9. Construir respuesta estructurada
        top_offenders_summary = []
        for offender, _ in created_offenders:
            top_offenders_summary.append({
                "id": offender.id,
                "rank_position": offender.rank_position,
                "category_id": offender.category_id,
                "category_name": category_names.get(offender.category_id, "Desconocida"),
                "canonical_description": offender.canonical_description,
                "occurrence_count": offender.occurrence_count,
                "percentage_of_total": offender.percentage_of_total,
            })

        return {
            "report_id": report.id,
            "period": report.period,
            "total_discrepancies": total_discrepancies,
            "total_clusters": len(created_offenders),
            "top_offenders": top_offenders_summary,
            "message": (
                f"Agrupamiento completado exitosamente: {len(created_offenders)} Top Offenders detectados "
                f"a partir de {total_discrepancies} discrepancias en el periodo {report.period}."
            ),
        }

