import React from 'react';
import { Calendar, AlertCircle, Clock, CalendarDays } from 'lucide-react';
import type { ReceivablesSummary } from '../../lib/api/finance';

interface ReceivablesSummaryCardProps {
  data: ReceivablesSummary;
  onViewDetails?: () => void;
}

const ReceivablesSummaryCard: React.FC<ReceivablesSummaryCardProps> = ({ data, onViewDetails }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  return (
    <div className="mb-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Posição de Contas a Receber</h2>
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Vencido */}
          <div
            className={`p-4 rounded-lg border-l-4 ${data.overdue > 0 ? 'bg-yellow-50 border-yellow-500' : 'bg-gray-50 border-gray-300'}`}
          >
            <div className="flex items-center space-x-2 mb-2">
              <AlertCircle className={`w-5 h-5 ${data.overdue > 0 ? 'text-yellow-500' : 'text-gray-400'}`} />
              <span className={`text-sm font-medium ${data.overdue > 0 ? 'text-yellow-800' : 'text-gray-600'}`}>
                Vencido
              </span>
            </div>
            <p className={`text-xl font-bold ${data.overdue > 0 ? 'text-yellow-600' : 'text-gray-500'}`}>
              {formatCurrency(data.overdue)}
            </p>
          </div>

          {/* Vence hoje */}
          <div
            className={`p-4 rounded-lg border-l-4 ${data.due_today > 0 ? 'bg-green-50 border-green-500' : 'bg-gray-50 border-gray-300'}`}
          >
            <div className="flex items-center space-x-2 mb-2">
              <Clock className={`w-5 h-5 ${data.due_today > 0 ? 'text-green-500' : 'text-gray-400'}`} />
              <span className={`text-sm font-medium ${data.due_today > 0 ? 'text-green-800' : 'text-gray-600'}`}>
                A Receber Hoje
              </span>
            </div>
            <p className={`text-xl font-bold ${data.due_today > 0 ? 'text-green-600' : 'text-gray-500'}`}>
              {formatCurrency(data.due_today)}
            </p>
          </div>

          {/* Próximos 7 dias */}
          <div className="p-4 rounded-lg border-l-4 border-blue-300 bg-blue-50">
            <div className="flex items-center space-x-2 mb-2">
              <Calendar className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-medium text-blue-800">Próximos 7 dias</span>
            </div>
            <p className="text-xl font-bold text-blue-600">{formatCurrency(data.next_7_days)}</p>
          </div>

          {/* Próximos 30 dias */}
          <div className="p-4 rounded-lg border-l-4 border-indigo-300 bg-indigo-50">
            <div className="flex items-center space-x-2 mb-2">
              <CalendarDays className="w-5 h-5 text-indigo-500" />
              <span className="text-sm font-medium text-indigo-800">Próximos 30 dias</span>
            </div>
            <p className="text-xl font-bold text-indigo-600">{formatCurrency(data.next_30_days)}</p>
          </div>
        </div>

        {data.overdue > 0 && onViewDetails && (
          <div className="mt-4 pt-4 border-t">
            <button
              onClick={onViewDetails}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Ver detalhes →
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReceivablesSummaryCard;

