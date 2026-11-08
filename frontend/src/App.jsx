import React, { useState } from 'react';
import Layout from './components/Layout';
import UploadSection from './components/UploadSection';
import DashboardCards from './components/DashboardCards';
import TopOffendersTable from './components/TopOffendersTable';
import { uploadExcel, runNLPClustering, downloadReport } from './services/api';
import { 
  FileDown, 
  Cpu, 
  CheckCircle2, 
  AlertCircle, 
  RotateCcw, 
  Loader2, 
  Sparkles 
} from 'lucide-react';

export default function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [reportData, setReportData] = useState(null);
  const [nlpData, setNlpData] = useState(null);

  const [isUploading, setIsUploading] = useState(false);
  const [isClustering, setIsClustering] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Parsear mensajes de error claros provenientes de FastAPI / Axios
  const extractErrorMessage = (err) => {
    if (err.response) {
      if (err.response.status === 409) {
        return err.response.data?.detail || 'Archivo Duplicado: Este reporte Excel ya ha sido procesado previamente.';
      }
      if (err.response.status === 422) {
        return err.response.data?.detail || 'Error de Validación: El archivo no cumple con el formato o columnas requeridas.';
      }
      if (err.response.status === 404) {
        return err.response.data?.detail || 'Recurso no encontrado en el servidor.';
      }
      return err.response.data?.detail || `Error en el servidor (${err.response.status}).`;
    }
    if (err.request) {
      return 'No se pudo conectar con el servidor backend. Asegúrate de que FastAPI esté activo en http://127.0.0.1:8000';
    }
    return err.message || 'Ocurrió un error inesperado.';
  };

  // Paso 1: Subir Archivo Excel
  const handleUpload = async (file, period) => {
    setIsUploading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const data = await uploadExcel(file, period);
      setReportData(data);
      setCurrentStep(2);
      setSuccessMessage(
        `Reporte '${data.filename}' cargado exitosamente (${data.total_discrepancies} discrepancias registradas).`
      );

      // Disparar automáticamente el análisis NLP para una experiencia fluida
      await executeNLP(data.report_id);
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setIsUploading(false);
    }
  };

  // Paso 2: Ejecutar Agrupamiento NLP
  const executeNLP = async (reportId) => {
    const id = reportId || reportData?.report_id;
    if (!id) return;

    setIsClustering(true);
    setErrorMessage(null);

    try {
      const data = await runNLPClustering(id);
      setNlpData(data);
      setCurrentStep(4);
      setSuccessMessage(
        `Agrupamiento NLP finalizado: Se identificaron ${data.total_clusters} clústeres de Top Offenders.`
      );
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setIsClustering(false);
    }
  };

  // Paso 4: Descargar Presentación PowerPoint
  const handleDownloadPPTX = async () => {
    if (!reportData?.report_id) return;
    setIsDownloading(true);
    setErrorMessage(null);

    try {
      await downloadReport(reportData.report_id, reportData.period);
      setSuccessMessage('Presentación ejecutiva PowerPoint (.pptx) descargada con éxito.');
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setIsDownloading(false);
    }
  };

  // Reiniciar flujo para un nuevo reporte
  const handleReset = () => {
    setReportData(null);
    setNlpData(null);
    setCurrentStep(1);
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  return (
    <Layout currentStep={currentStep}>
      {/* Notificación de Éxito Global */}
      {successMessage && (
        <div className="p-3.5 bg-emerald-950/40 border border-emerald-800/80 rounded-xl flex items-center justify-between text-xs text-emerald-200 shadow-sm animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button 
            onClick={() => setSuccessMessage(null)}
            className="text-emerald-400 hover:text-emerald-200 text-xs ml-4"
          >
            &times;
          </button>
        </div>
      )}

      {/* Notificación de Error Global */}
      {errorMessage && (
        <div className="p-3.5 bg-red-950/40 border border-red-800/80 rounded-xl flex items-center justify-between text-xs text-red-200 shadow-sm animate-fade-in">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button 
            onClick={() => setErrorMessage(null)}
            className="text-red-400 hover:text-red-200 text-xs ml-4"
          >
            &times;
          </button>
        </div>
      )}

      {/* Sección 1: Ingesta del Excel (Siempre visible o en modo colapsable) */}
      {!reportData ? (
        <UploadSection 
          onUploadSuccess={handleUpload} 
          isLoading={isUploading || isClustering}
          errorMessage={errorMessage}
        />
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white">
                Reporte Activo: <span className="text-emerald-400">{reportData.filename}</span>
              </h4>
              <p className="text-xs text-slate-400">
                Periodo: <span className="font-semibold text-slate-300">{reportData.period}</span> &bull; 
                Report ID #{reportData.report_id} &bull; 
                {reportData.total_discrepancies} discrepancias registradas
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Botón para re-ejecutar NLP si se desea */}
            <button
              onClick={() => executeNLP(reportData.report_id)}
              disabled={isClustering}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1.5 transition-colors border border-slate-700"
            >
              {isClustering ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
                  <span>Re-agrupando...</span>
                </>
              ) : (
                <>
                  <Cpu className="w-3.5 h-3.5 text-blue-400" />
                  <span>Re-procesar NLP</span>
                </>
              )}
            </button>

            {/* Botón para cargar nuevo archivo */}
            <button
              onClick={handleReset}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1.5 transition-colors border border-slate-700"
            >
              <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
              <span>Cargar Otro Excel</span>
            </button>
          </div>
        </div>
      )}

      {/* Barra de Progreso del Motor NLP cuando está procesando */}
      {isClustering && (
        <div className="bg-slate-900 border border-blue-900/50 rounded-xl p-5 text-center space-y-3 shadow-lg shadow-blue-950/20">
          <div className="flex items-center justify-center space-x-2 text-blue-400">
            <Sparkles className="w-5 h-5 animate-pulse" />
            <h4 className="text-sm font-semibold text-white">
              Motor de Inteligencia Artificial en Ejecución
            </h4>
          </div>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Generando embeddings densos con <span className="text-blue-300 font-mono">MiniLM-L12-v2</span> y calculando medoides semánticos por categoría temática...
          </p>
          <div className="w-48 h-1 bg-slate-800 rounded-full mx-auto overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full animate-pulse w-3/4"></div>
          </div>
        </div>
      )}

      {/* Sección 2: KPIs y Tarjetas de Resumen */}
      <DashboardCards
        totalDiscrepancies={reportData ? reportData.total_discrepancies : 0}
        totalClusters={nlpData ? nlpData.total_clusters : 0}
        nlpStatus={nlpData ? 'Completado' : isClustering ? 'Procesando...' : 'Pendiente'}
        period={reportData ? reportData.period : 'N/A'}
      />

      {/* Sección 3: Botón de Exportación Ejecutiva a PowerPoint */}
      {nlpData && (
        <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-blue-950/40 border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row items-center justify-between gap-4 shadow-sm">
          <div>
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <FileDown className="w-4 h-4 text-purple-400" />
              Presentación Ejecutiva PowerPoint (.pptx)
            </h4>
            <p className="text-xs text-slate-400 mt-1">
              Incluye portada corporativa, resumen general de métricas, gráfica de pastel y el desglose de los Top 5 problemas recurrentes.
            </p>
          </div>

          <button
            onClick={handleDownloadPPTX}
            disabled={isDownloading}
            className="px-5 py-2.5 rounded-lg text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white flex items-center space-x-2 transition-all shadow-md shadow-purple-600/20 shrink-0"
          >
            {isDownloading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Generando PowerPoint...</span>
              </>
            ) : (
              <>
                <FileDown className="w-4 h-4" />
                <span>Descargar Presentación (.pptx)</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Sección 4: Tabla y Gráficos de Top Offenders */}
      <TopOffendersTable topOffenders={nlpData ? nlpData.top_offenders : []} />
    </Layout>
  );
}

