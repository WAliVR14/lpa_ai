import React from 'react';
import { AlertTriangle, Layers, Cpu, CheckCircle, Clock } from 'lucide-react';

export default function DashboardCards({ 
  totalDiscrepancies = 0, 
  totalClusters = 0, 
  nlpStatus = 'Pendiente', 
  period = 'N/A' 
}) {
  const isCompleted = nlpStatus === 'Completado';

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
      {/* KPI 1: Total de Discrepancias */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400">Total de Discrepancias</p>
            <h3 className="text-2xl font-bold text-white mt-1">
              {totalDiscrepancies.toLocaleString()}
            </h3>
            <p className="text-[11px] text-slate-400 mt-1">
              Hallazgos registrados en el periodo <span className="text-slate-300 font-semibold">{period}</span>
            </p>
          </div>
          <div className="w-11 h-11 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500/40"></div>
      </div>

      {/* KPI 2: Total de Clústeres */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400">Total de Clústeres</p>
            <h3 className="text-2xl font-bold text-white mt-1">
              {totalClusters}
            </h3>
            <p className="text-[11px] text-slate-400 mt-1">
              Patrones semánticos identificados
            </p>
          </div>
          <div className="w-11 h-11 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Layers className="w-5 h-5" />
          </div>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500/40"></div>
      </div>

      {/* KPI 3: Estado del NLP */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400">Estado del Motor NLP</p>
            <div className="flex items-center space-x-2 mt-1">
              <span className={`inline-flex items-center gap-1.5 text-sm font-bold ${
                isCompleted ? 'text-emerald-400' : 'text-amber-400'
              }`}>
                {isCompleted ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    Completado
                  </>
                ) : (
                  <>
                    <Clock className="w-4 h-4 text-amber-400" />
                    {nlpStatus}
                  </>
                )}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              {isCompleted ? 'Medoides calculados exitosamente' : 'Pendiente de ejecución NLP'}
            </p>
          </div>
          <div className={`w-11 h-11 rounded-lg flex items-center justify-center ${
            isCompleted 
              ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' 
              : 'bg-amber-500/10 border border-amber-500/20 text-amber-400'
          }`}>
            <Cpu className="w-5 h-5" />
          </div>
        </div>
        <div className={`absolute bottom-0 left-0 right-0 h-0.5 ${
          isCompleted ? 'bg-emerald-500/40' : 'bg-amber-500/40'
        }`}></div>
      </div>
    </div>
  );
}

