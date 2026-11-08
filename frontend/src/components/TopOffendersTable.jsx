import React from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  Cell 
} from 'recharts';
import { Award, TrendingUp, Tag, FileText } from 'lucide-react';

const BAR_COLORS = ['#3b82f6', '#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'];

export default function TopOffendersTable({ topOffenders = [] }) {
  if (!topOffenders || topOffenders.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
        <FileText className="w-8 h-8 text-slate-400 mx-auto mb-2" />
        <p className="text-sm font-medium">No hay Top Offenders calculados aún.</p>
        <p className="text-xs text-slate-400 mt-1">Sube un reporte y ejecuta el agrupamiento semántico para visualizar los problemas recurrentes.</p>
      </div>
    );
  }

  // Preparar datos para el gráfico de barras (Top 5)
  const chartData = topOffenders.slice(0, 5).map((item) => ({
    name: `Rank #${item.rank_position}`,
    category: item.category_name,
    ocurrencias: item.occurrence_count,
    porcentaje: item.percentage_of_total,
    shortDesc: item.canonical_description.length > 35 
      ? item.canonical_description.slice(0, 35) + '...' 
      : item.canonical_description,
  }));

  const getRankBadge = (rank) => {
    switch (rank) {
      case 1:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
            <Award className="w-3.5 h-3.5 text-amber-400" /> Rank #1
          </span>
        );
      case 2:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-slate-400/20 text-slate-200 border border-slate-400/30">
            Rank #2
          </span>
        );
      case 3:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-amber-700/20 text-amber-400 border border-amber-700/30">
            Rank #3
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
            Rank #{rank}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Gráfico de Barras Superior (Visualización Rápida de los Top 5) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-semibold text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            Concentración de Hallazgos en Top Offenders
          </h4>
          <span className="text-xs text-slate-400 font-mono">Top {chartData.length} Clústeres Críticos</span>
        </div>

        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#0f172a', 
                  borderColor: '#334155', 
                  borderRadius: '8px',
                  color: '#f8fafc',
                  fontSize: '12px' 
                }}
                formatter={(val, name, props) => [
                  `${val} hallazgos (${props.payload.porcentaje}%)`, 
                  props.payload.category
                ]}
                labelFormatter={(label) => `${label}`}
              />
              <Bar dataKey="ocurrencias" radius={[6, 6, 0, 0]}>
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tabla Detallada */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div>
            <h4 className="text-sm font-semibold text-white">Detalle de Clústeres Semánticos Detectados</h4>
            <p className="text-xs text-slate-400 mt-0.5">Medoides representativos calculados mediante distancia coseno &le; 0.22</p>
          </div>
          <span className="text-xs text-slate-400 bg-slate-800 px-2.5 py-1 rounded-md font-medium">
            {topOffenders.length} Clústeres
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th scope="col" className="px-5 py-3.5 font-semibold">Prioridad</th>
                <th scope="col" className="px-5 py-3.5 font-semibold">Categoría Temática</th>
                <th scope="col" className="px-5 py-3.5 font-semibold">Descripción Canónica (Medoide NLP)</th>
                <th scope="col" className="px-5 py-3.5 font-semibold text-center">Frecuencia</th>
                <th scope="col" className="px-5 py-3.5 font-semibold text-right">% Impacto</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {topOffenders.map((offender) => (
                <tr key={offender.id} className="hover:bg-slate-800/40 transition-colors">
                  {/* Rank */}
                  <td className="px-5 py-4 whitespace-nowrap">
                    {getRankBadge(offender.rank_position)}
                  </td>

                  {/* Categoría */}
                  <td className="px-5 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium bg-slate-800 text-slate-200 border border-slate-700/60">
                      <Tag className="w-3 h-3 text-blue-400" />
                      {offender.category_name}
                    </span>
                  </td>

                  {/* Descripción Canónica */}
                  <td className="px-5 py-4 max-w-md">
                    <p className="font-medium text-slate-100 leading-relaxed text-xs">
                      "{offender.canonical_description}"
                    </p>
                  </td>

                  {/* Ocurrencias */}
                  <td className="px-5 py-4 text-center whitespace-nowrap font-mono font-semibold text-white">
                    <span className="px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700/60">
                      {offender.occurrence_count}
                    </span>
                  </td>

                  {/* Porcentaje de Impacto con barra */}
                  <td className="px-5 py-4 text-right whitespace-nowrap">
                    <div className="flex items-center justify-end space-x-2">
                      <span className="font-semibold text-blue-400 font-mono">
                        {offender.percentage_of_total.toFixed(1)}%
                      </span>
                      <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${Math.min(100, offender.percentage_of_total * 2)}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

