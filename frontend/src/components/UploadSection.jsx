import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

export default function UploadSection({ onUploadSuccess, isLoading, errorMessage }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [period, setPeriod] = useState('2026-Q3');
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
      setSelectedFile(file);
    } else {
      alert('Por favor selecciona un archivo con extensión .xlsx o .xls');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedFile) return;
    onUploadSuccess(selectedFile, period.trim());
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
            Ingesta de Reporte Excel LPA
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Sube el archivo trimestral exportado del sistema Aumovio para su limpieza ETL y análisis semántico.
          </p>
        </div>
      </div>

      {errorMessage && (
        <div className="mb-4 p-3 bg-red-950/50 border border-red-800/80 rounded-lg flex items-start gap-2.5 text-xs text-red-200">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold">Error en la operación: </span>
            <span>{errorMessage}</span>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Campo de Periodo */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300">
              Periodo de Evaluación
            </label>
            <input
              type="text"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              placeholder="Ej. 2026-Q3"
              pattern="^\d{4}-Q[1-4]$"
              title="Formato requerido: AAAA-QX (ej. 2026-Q3)"
              className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <p className="text-[11px] text-slate-400">Formato: AAAA-QT (ej. 2026-Q3)</p>
          </div>

          {/* Zona de Drag & Drop */}
          <div className="md:col-span-2">
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
                dragActive
                  ? 'border-blue-500 bg-blue-950/20'
                  : selectedFile
                  ? 'border-emerald-600/60 bg-emerald-950/10'
                  : 'border-slate-700 hover:border-slate-600 bg-slate-950/40'
              }`}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".xlsx, .xls"
                onChange={handleChange}
                className="hidden"
              />

              {selectedFile ? (
                <div className="flex items-center justify-center space-x-3 text-emerald-400 text-xs">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                  <div className="text-left truncate">
                    <span className="font-semibold block truncate text-slate-200">{selectedFile.name}</span>
                    <span className="text-slate-400 text-[11px]">
                      {(selectedFile.size / 1024).toFixed(1)} KB &bull; Listo para procesar
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFile(null);
                    }}
                    className="ml-2 text-slate-400 hover:text-red-400 text-xs underline"
                  >
                    Cambiar
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-1">
                  <UploadCloud className="w-6 h-6 text-slate-400 mb-1.5" />
                  <p className="text-xs text-slate-300 font-medium">
                    Arrastra aquí el archivo Excel o <span className="text-blue-400 underline">haz clic para examinar</span>
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">Soporta hojas con formato oficial LPA Aumovio (.xlsx)</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Botón de Enviar */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={!selectedFile || isLoading}
            className={`px-5 py-2.5 rounded-lg text-xs font-semibold flex items-center space-x-2 transition-all shadow-md ${
              !selectedFile || isLoading
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/20'
            }`}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Procesando Ingesta ETL...</span>
              </>
            ) : (
              <>
                <FileSpreadsheet className="w-4 h-4" />
                <span>Subir y Procesar Reporte</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

