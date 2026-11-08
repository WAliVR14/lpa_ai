import io
import tempfile
from pathlib import Path
from typing import Any

import matplotlib
# Configuración del backend 'Agg' para renderizado headless sin interfaz gráfica
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.lpa_models import Category, Discrepancy, Report, TopOffender


class ReportService:
    """
    Servicio de Reportería Ejecutiva y Generación de Presentaciones PPTX.
    Genera presentaciones ejecutivas con estilo corporativo automotriz
    basadas en los resultados del motor de NLP y los Top Offenders detectados.
    """

    # Paleta Corporativa Automotriz (Navy, Slate, Acero y Acento)
    COLOR_PRIMARY_NAVY = RGBColor(0, 45, 98)       # #002D62 - Azul marino profundo
    COLOR_SECONDARY_BLUE = RGBColor(43, 108, 176)   # #2B6CB0 - Azul secundario
    COLOR_DARK_TEXT = RGBColor(26, 32, 44)         # #1A202C - Texto oscuro principal
    COLOR_MUTED_TEXT = RGBColor(74, 85, 104)       # #4A5568 - Texto secundario/slate
    COLOR_CARD_BG = RGBColor(248, 250, 252)        # #F8FAFC - Fondo de tarjeta claro
    COLOR_BORDER = RGBColor(226, 232, 240)         # #E2E8F0 - Borde sutil
    COLOR_ACCENT_AMBER = RGBColor(217, 119, 6)     # #D97706 - Acento de alerta/impacto
    COLOR_WHITE = RGBColor(255, 255, 255)

    @classmethod
    def generate_pptx_report(cls, db: Session, report_id: int) -> str:
        """
        Genera la presentación ejecutiva en formato PowerPoint (.pptx):
        1. Consulta el reporte y sus métricas principales.
        2. Extrae el Top 5 de TopOffenders por impacto y frecuencia.
        3. Construye un gráfico de pastel circular de categorías con Matplotlib.
        4. Compone los slides: Portada, Resumen Ejecutivo y Detalle por cada Top Offender.
        5. Guarda en un archivo temporal y retorna su ruta física.
        """
        # 1. Consultar Reporte
        report = db.execute(select(Report).where(Report.id == report_id)).scalar_one_or_none()
        if not report:
            raise ValueError(f"Reporte con ID #{report_id} no encontrado.")

        # 2. Consultar Top 5 TopOffenders del reporte
        top_offenders = db.execute(
            select(TopOffender)
            .options(joinedload(TopOffender.category))
            .where(TopOffender.report_id == report_id)
            .order_by(TopOffender.rank_position.asc(), TopOffender.occurrence_count.desc())
            .limit(5)
        ).scalars().all()

        if not top_offenders:
            raise ValueError(
                f"El reporte #{report_id} ({report.period}) no contiene Top Offenders calculados. "
                "Ejecute primero el agrupamiento NLP antes de generar la presentación."
            )

        # 3. Distribución de discrepancias por Categoría para el gráfico
        category_distribution = db.execute(
            select(Category.name, func.count(Discrepancy.id))
            .join(Discrepancy, Discrepancy.category_id == Category.id)
            .where(Discrepancy.report_id == report_id)
            .group_by(Category.name)
            .order_by(func.count(Discrepancy.id).desc())
        ).all()

        # 4. Generar gráfico de pastel con Matplotlib en memoria
        chart_stream = cls._generate_category_pie_chart(category_distribution)

        # 5. Construcción de la presentación PPTX
        prs = Presentation()
        # Formato panorámico moderno 16:9 (13.33 x 7.5 pulgadas)
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        # 5.1 Slide 1: Portada Corporativa
        cls._build_cover_slide(prs, report.period)

        # 5.2 Slide 2: Resumen Ejecutivo y Gráfico
        cls._build_summary_slide(
            prs=prs,
            period=report.period,
            total_discrepancies=report.total_discrepancies,
            total_categories=len(category_distribution),
            top_offenders=top_offenders,
            chart_stream=chart_stream,
        )

        # 5.3 Slides 3 a N: Detalle de cada uno de los Top 5 problemas
        for offender in top_offenders:
            cls._build_top_offender_slide(prs, offender)

        # 6. Guardar archivo temporal en disco
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
        temp_path = Path(temp_file.name)
        temp_file.close()

        prs.save(str(temp_path))
        return str(temp_path)

    @classmethod
    def _generate_category_pie_chart(cls, category_distribution: list[Any]) -> io.BytesIO:
        """Genera un gráfico de pastel circular corporativo en memoria."""
        plt.switch_backend("Agg")

        if not category_distribution:
            # Gráfico de respaldo si no hay datos
            fig, ax = plt.subplots(figsize=(6, 4.5), dpi=150)
            ax.text(0.5, 0.5, "Sin datos de categorías", ha="center", va="center")
            stream = io.BytesIO()
            fig.savefig(stream, format="png", bbox_inches="tight")
            plt.close(fig)
            stream.seek(0)
            return stream

        # Si hay más de 5 categorías, consolidar las menores en 'Otras'
        labels: list[str] = []
        values: list[int] = []
        other_count = 0

        for i, (cat_name, count) in enumerate(category_distribution):
            if i < 5:
                labels.append(cat_name)
                values.append(count)
            else:
                other_count += count

        if other_count > 0:
            labels.append("Otras Categorías")
            values.append(other_count)

        fig, ax = plt.subplots(figsize=(6.2, 4.8), dpi=200, facecolor="#F8FAFC")
        palette = ["#002D62", "#2B6CB0", "#4A5568", "#0D9488", "#D97706", "#718096"]

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=palette[: len(values)],
            wedgeprops=dict(width=0.7, edgecolor="white", linewidth=2),
            textprops=dict(color="#1A202C", fontsize=9, fontweight="medium"),
            pctdistance=0.75,
        )

        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
            autotext.set_fontsize(9)

        ax.set_title(
            "Distribución de Discrepancias por Categoría",
            fontsize=12,
            fontweight="bold",
            color="#002D62",
            pad=14,
        )

        chart_stream = io.BytesIO()
        fig.savefig(chart_stream, format="png", bbox_inches="tight", facecolor="#F8FAFC")
        plt.close(fig)
        chart_stream.seek(0)
        return chart_stream

    @classmethod
    def _build_cover_slide(cls, prs: Presentation, period: str):
        """Construye un slide de portada sobrio y elegante."""
        blank_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_layout)

        # Barra decorativa lateral superior
        top_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.4)
        )
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = cls.COLOR_PRIMARY_NAVY
        top_bar.line.fill.background()

        # Recuadro principal
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.8), Inches(10.9), Inches(4.2)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = cls.COLOR_CARD_BG
        card.line.color.rgb = cls.COLOR_BORDER
        card.line.width = Pt(1.5)

        # Título principal
        title_box = slide.shapes.add_textbox(Inches(1.8), Inches(2.3), Inches(9.7), Inches(1.5))
        tf = title_box.text_frame
        tf.word_wrap = True
        p_title = tf.paragraphs[0]
        p_title.text = f"Resumen Trimestral LPA - {period}"
        p_title.font.size = Pt(36)
        p_title.font.bold = True
        p_title.font.color.rgb = cls.COLOR_PRIMARY_NAVY
        p_title.font.name = "Calibri"

        # Subtítulo institucional
        subtitle_box = slide.shapes.add_textbox(Inches(1.8), Inches(3.8), Inches(9.7), Inches(1.8))
        tf_sub = subtitle_box.text_frame
        tf_sub.word_wrap = True
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = (
            "Sistema Integral de Inteligencia Artificial y Detección de Top Offenders\n"
            "Dirección de Aseguramiento de Calidad & Excelencia Operativa | Aumovio"
        )
        p_sub.font.size = Pt(16)
        p_sub.font.color.rgb = cls.COLOR_MUTED_TEXT
        p_sub.font.name = "Calibri"

        # Pie de página de portada
        footer_box = slide.shapes.add_textbox(Inches(1.8), Inches(6.4), Inches(9.7), Inches(0.6))
        tf_foot = footer_box.text_frame
        p_foot = tf_foot.paragraphs[0]
        p_foot.text = "Documento Confidencial de Uso Interno - Generado automáticamente por lpa_ai"
        p_foot.font.size = Pt(10)
        p_foot.font.color.rgb = cls.COLOR_MUTED_TEXT

    @classmethod
    def _build_summary_slide(
        cls,
        prs: Presentation,
        period: str,
        total_discrepancies: int,
        total_categories: int,
        top_offenders: list[TopOffender],
        chart_stream: io.BytesIO,
    ):
        """Slide ejecutivo con métricas de resumen y gráfico de pastel."""
        blank_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_layout)

        # Encabezado estándar
        cls._add_slide_header(slide, "Resumen Ejecutivo de Auditorías LPA", f"Periodo: {period}")

        # Tarjeta izquierda: Indicadores Clave (KPIs)
        kpi_card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.3)
        )
        kpi_card.fill.solid()
        kpi_card.fill.fore_color.rgb = cls.COLOR_CARD_BG
        kpi_card.line.color.rgb = cls.COLOR_BORDER
        kpi_card.line.width = Pt(1)

        # Texto de KPIs
        kpi_box = slide.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(4.8), Inches(4.7))
        tf = kpi_box.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = "Métricas Generales del Periodo"
        p1.font.size = Pt(20)
        p1.font.bold = True
        p1.font.color.rgb = cls.COLOR_PRIMARY_NAVY
        p1.space_after = Pt(14)

        top5_sum = sum(o.occurrence_count for o in top_offenders)
        top5_pct = (top5_sum / total_discrepancies * 100) if total_discrepancies > 0 else 0.0

        metrics = [
            ("Total de Discrepancias Auditadas:", f"{total_discrepancies:,} hallazgos"),
            ("Categorías Impactadas:", f"{total_categories} áreas temáticas"),
            ("Top Offenders Identificados:", f"{len(top_offenders)} clústeres críticos"),
            ("Concentración en Top 5:", f"{top5_pct:.1f}% del total global"),
        ]

        for label, val in metrics:
            p_label = tf.add_paragraph()
            p_label.text = label
            p_label.font.size = Pt(12)
            p_label.font.bold = True
            p_label.font.color.rgb = cls.COLOR_MUTED_TEXT

            p_val = tf.add_paragraph()
            p_val.text = val
            p_val.font.size = Pt(18)
            p_val.font.bold = True
            p_val.font.color.rgb = cls.COLOR_SECONDARY_BLUE
            p_val.space_after = Pt(10)

        # Lado derecho: Inserción del Gráfico de Pastel
        slide.shapes.add_picture(
            chart_stream,
            left=Inches(6.6),
            top=Inches(1.5),
            width=Inches(6.0),
            height=Inches(5.3),
        )

    @classmethod
    def _build_top_offender_slide(cls, prs: Presentation, offender: TopOffender):
        """Construye un slide específico para un Top Offender del Top 5."""
        blank_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_layout)

        category_name = offender.category.name if offender.category else "Categoría General"

        # Encabezado
        cls._add_slide_header(
            slide,
            f"Top Offender #{offender.rank_position}: {category_name}",
            f"Análisis Semántico Automatizado de Causa Raíz",
        )

        # Tarjeta Principal (Contenedor)
        main_card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.3)
        )
        main_card.fill.solid()
        main_card.fill.fore_color.rgb = cls.COLOR_CARD_BG
        main_card.line.color.rgb = cls.COLOR_BORDER
        main_card.line.width = Pt(1)

        # Métricas de Impacto (Badges superiores)
        badge_box = slide.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(10.9), Inches(0.8))
        tf_badge = badge_box.text_frame
        p_badge = tf_badge.paragraphs[0]
        p_badge.text = (
            f"Frecuencia: {offender.occurrence_count} hallazgos agrupados   |   "
            f"Impacto: {offender.percentage_of_total:.1f}% del total del trimestre   |   "
            f"Prioridad: Rank #{offender.rank_position}"
        )
        p_badge.font.size = Pt(14)
        p_badge.font.bold = True
        p_badge.font.color.rgb = cls.COLOR_ACCENT_AMBER

        # Título de Sección del Medoide
        header_box = slide.shapes.add_textbox(Inches(1.2), Inches(2.7), Inches(10.9), Inches(0.5))
        tf_header = header_box.text_frame
        p_h = tf_header.paragraphs[0]
        p_h.text = "Descripción Canónica del Hallazgo (Medoide del Clúster):"
        p_h.font.size = Pt(15)
        p_h.font.bold = True
        p_h.font.color.rgb = cls.COLOR_PRIMARY_NAVY

        # Caja de la Descripción Canónica
        desc_box = slide.shapes.add_textbox(Inches(1.2), Inches(3.3), Inches(10.9), Inches(2.0))
        tf_desc = desc_box.text_frame
        tf_desc.word_wrap = True
        p_desc = tf_desc.paragraphs[0]
        p_desc.text = f'"{offender.canonical_description}"'
        p_desc.font.size = Pt(18)
        p_desc.font.italic = True
        p_desc.font.color.rgb = cls.COLOR_DARK_TEXT
        p_desc.space_after = Pt(14)

        # Recomendación Operativa
        rec_box = slide.shapes.add_textbox(Inches(1.2), Inches(5.3), Inches(10.9), Inches(1.2))
        tf_rec = rec_box.text_frame
        tf_rec.word_wrap = True
        p_rec_title = tf_rec.paragraphs[0]
        p_rec_title.text = "Acción Recomendada para Cierre:"
        p_rec_title.font.size = Pt(13)
        p_rec_title.font.bold = True
        p_rec_title.font.color.rgb = cls.COLOR_SECONDARY_BLUE

        p_rec_text = tf_rec.add_paragraph()
        p_rec_text.text = (
            "Implementar plan de contención inmediata en las estaciones afectadas, auditar el proceso "
            "de acuerdo a la matriz LPA y reforzar el estándar operacional con el personal involucrado."
        )
        p_rec_text.font.size = Pt(12)
        p_rec_text.font.color.rgb = cls.COLOR_MUTED_TEXT

    @classmethod
    def _add_slide_header(cls, slide, title_text: str, subtitle_text: str):
        """Agrega encabezado uniforme con línea divisoria corporativa."""
        # Barra superior decorativa
        top_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.15)
        )
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = cls.COLOR_PRIMARY_NAVY
        top_bar.line.fill.background()

        # Texto del título
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.9))
        tf = title_box.text_frame
        tf.word_wrap = True
        p_title = tf.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = cls.COLOR_PRIMARY_NAVY
        p_title.font.name = "Calibri"

        p_sub = tf.add_paragraph()
        p_sub.text = subtitle_text
        p_sub.font.size = Pt(12)
        p_sub.font.color.rgb = cls.COLOR_MUTED_TEXT
        p_sub.font.name = "Calibri"

