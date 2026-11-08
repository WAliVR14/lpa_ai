import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1',
  timeout: 120000, // 2 minutos para procesamiento de IA
});

/**
 * Sube el archivo Excel de auditorías LPA con el periodo especificado.
 * @param {File} file - Archivo .xlsx
 * @param {string} period - Ej. '2026-Q3'
 */
export const uploadExcel = async (file, period) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post(`/reports/upload?period=${encodeURIComponent(period)}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Ejecuta el agrupamiento semántico NLP para descubrir los Top Offenders de un reporte.
 * @param {number} reportId
 */
export const runNLPClustering = async (reportId) => {
  const response = await api.post(`/nlp/cluster/${reportId}`);
  return response.data;
};

/**
 * Descarga la presentación ejecutiva en PowerPoint (.pptx).
 * @param {number} reportId
 * @param {string} period
 */
export const downloadReport = async (reportId, period = 'Trimestre') => {
  const response = await api.get(`/reports/download/${reportId}`, {
    responseType: 'blob',
  });

  // Generar descarga directa en el navegador
  const blob = new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `Reporte_Ejecutivo_LPA_${period}.pptx`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
  return true;
};

export default api;

