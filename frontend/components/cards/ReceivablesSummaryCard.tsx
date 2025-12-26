import React from 'react';
import { AlertCircle, CalendarDays } from 'lucide-react';
import type { ReceivablesSummary } from '../../lib/api/finance';

interface ReceivablesSummaryCardProps {
  data: ReceivablesSummary;
  onViewDetails?: () => void;
}

const ReceivablesSummaryCard: React.FC<ReceivablesSummaryCardProps> = ({ data, onViewDetails }) => {
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(val);
  };

  return (
    <div className="mb-6 h-full flex flex-col">
      {/* Título do bloco */}
      <h2 className="text-xl font-bold mb-4 text-gray-800">Contas a Receber</h2>

      {/* Container simplificado - apenas totais */}
      <div className="bg-white rounded-lg shadow-md p-6 flex-1">
        <div className="space-y-4">
          {/* Total Vencido */}
          <div className={`p-4 rounded-lg border-l-4 ${data.overdue > 0 ? 'bg-red-50 border-red-500' : 'bg-gray-50 border-gray-300'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertCircle className={`w-5 h-5 ${data.overdue > 0 ? 'text-red-500' : 'text-gray-400'}`} />
                <span className={`text-sm font-medium ${data.overdue > 0 ? 'text-red-800' : 'text-gray-600'}`}>
                  Total Vencido
                </span>
              </div>
              <p className={`text-xl font-bold ${data.overdue > 0 ? 'text-red-600' : 'text-gray-500'}`}>
                {formatCurrency(data.overdue)}
              </p>
            </div>
          </div>

          {/* Total a Receber (próximos 30 dias) */}
          <div className="p-4 rounded-lg border-l-4 bg-green-50 border-green-300">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CalendarDays className="w-5 h-5 text-green-500" />
                <span className="text-sm font-medium text-green-800">
                  Total a Receber (próximos 30 dias)
                </span>
              </div>
              <p className="text-xl font-bold text-green-600">
                {formatCurrency(data.next_30_days)}
              </p>
            </div>
          </div>
        </div>

        {/* Botão de detalhes */}
        {onViewDetails && (
          <div className="mt-6 pt-4 border-t border-gray-200">
            <button
              onClick={onViewDetails}
              className="w-full text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors py-2 hover:bg-blue-50 rounded"
            >
              Ver detalhes (vence hoje, próximos 7 dias, lista completa) →
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReceivablesSummaryCard;
