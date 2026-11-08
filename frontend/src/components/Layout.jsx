import React from 'react';
import { 
  BarChart3, 
  FileSpreadsheet, 
  FileDown, 
  Cpu, 
  ShieldCheck, 
  Database,
  Layers,
  ChevronRight,
  Activity
} from 'lucide-react';

export default function Layout({ children, currentStep }) {
  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Lateral Corporativo */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 select-none">
        {/* Header del Sidebar */}
        <div className="h-16 px-5 border-b border-slate-800 flex items-center space-x-3 bg-slate-900/60">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-wide text-white">AUMOVIO LPA</h1>
            <p className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Quality AI Engine</p>
          </div>
        </div>

        {/* Navegación y Pasos */}
        <div className="flex-1 px-3 py-5 space-y-6 overflow-y-auto">
          <div>
            <span className="px-3 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Flujo Operativo
            </span>
            <nav className="mt-2 space-y-1">
              <div className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                currentStep >= 1 ? 'bg-slate-800 text-blue-400' : 'text-slate-400 hover:bg-slate-800/40'
              }`}>
                <div className="flex items-center space-x-2.5">
                  <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                  <span>1. Ingesta de Reporte</span>
                </div>
                {currentStep > 1 && <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">Listo</span>}
              </div>

              <div className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                currentStep >= 2 ? 'bg-slate-800 text-blue-400' : 'text-slate-400 hover:bg-slate-800/40'
              }`}>
                <div className="flex items-center space-x-2.5">
                  <Cpu className="w-4 h-4 text-indigo-400" />
                  <span>2. Análisis NLP & Medoides</span>
                </div>
                {currentStep > 2 && <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">Listo</span>}
              </div>

              <div className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                currentStep >= 3 ? 'bg-slate-800 text-blue-400' : 'text-slate-400 hover:bg-slate-800/40'
              }`}>
                <div className="flex items-center space-x-2.5">
                  <BarChart3 className="w-4 h-4 text-amber-400" />
                  <span>3. Top Offenders KPIs</span>
                </div>
                {currentStep >= 3 && <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">Activo</span>}
              </div>

              <div className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                currentStep >= 4 ? 'bg-slate-800 text-blue-400' : 'text-slate-400 hover:bg-slate-800/40'
              }`}>
                <div className="flex items-center space-x-2.5">
                  <FileDown className="w-4 h-4 text-purple-400" />
                  <span>4. Reporte PPTX</span>
                </div>
                {currentStep >= 4 && <span className="text-[10px] bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded">Exportar</span>}
              </div>
            </nav>
          </div>

          <div>
            <span className="px-3 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Arquitectura
            </span>
            <div className="mt-2 space-y-1.5 text-xs text-slate-400 px-3 py-2 bg-slate-950/40 rounded-lg border border-slate-800/60">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5"><Database className="w-3.5 h-3.5 text-slate-400" /> Base de Datos</span>
                <span className="text-emerald-400 text-[11px] font-mono">SQLite Local</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5"><Cpu className="w-3.5 h-3.5 text-slate-400" /> Modelo NLP</span>
                <span className="text-blue-400 text-[11px] font-mono">MiniLM-L12</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5"><Activity className="w-3.5 h-3.5 text-slate-400" /> Clustering</span>
                <span className="text-indigo-400 text-[11px] font-mono">Cosine &le; 0.22</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer del Sidebar */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/40 text-xs">
          <div className="flex items-center space-x-2 text-emerald-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>FastAPI Conectado</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5 font-mono">http://127.0.0.1:8000/api/v1</p>
        </div>
      </aside>

      {/* Área Principal */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header Superior */}
        <header className="h-16 bg-slate-900 border-b border-slate-800 px-8 flex items-center justify-between shrink-0 shadow-sm">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-900/40 text-blue-400 border border-blue-800/50">
              Control Panel
            </span>
            <ChevronRight className="w-4 h-4 text-slate-400" />
            <h2 className="text-sm font-semibold text-slate-200">
              Ingesta & Detección de Discrepancias LPA
            </h2>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-800/50 px-3 py-1.5 rounded-lg border border-slate-700/50">
              <ShieldCheck className="w-4 h-4 text-blue-400" />
              <span>Aumovio Quality Assurance</span>
            </div>
          </div>
        </header>

        {/* Contenido con scroll */}
        <main className="flex-1 overflow-y-auto p-8 space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
}

