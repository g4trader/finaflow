import React from 'react';
import { DollarSign, TrendingUp, TrendingDown } from 'lucide-react';
import type { OperationalAvailability } from '../../lib/api/finance';

interface CashAvailabilityCardsProps {
  data: OperationalAvailability;
}

const CashAvailabilityCards: React.FC<CashAvailabilityCardsProps> = ({ data }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const isNegative = data.total <= 0;
  const saldoConsolidado = data.saldo_consolidado ?? (data.total - (data.saldo_inicial ?? 0));

  return (
    <div className="mb-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Disponibilidade Financeira</h2>
      
      {/* Total Disponível - DESTAQUE PRINCIPAL */}
      <div className={`mb-4 rounded-xl shadow-lg p-8 border-2 ${isNegative ? 'bg-red-50 border-red-500' : 'bg-gradient-to-br from-indigo-50 to-blue-50 border-indigo-500'}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <DollarSign className={`w-8 h-8 ${isNegative ? 'text-red-600' : 'text-indigo-600'}`} />
            <span className={`text-lg font-semibold ${isNegative ? 'text-red-800' : 'text-indigo-800'}`}>
              Total Disponível
            </span>
          </div>
        </div>
        <p className={`text-4xl font-extrabold ${isNegative ? 'text-red-700' : 'text-indigo-900'}`}>
          {formatCurrency(data.total)}
        </p>
        {isNegative && (
          <p className="text-sm text-red-700 mt-2 font-medium">⚠️ Saldo negativo - Atenção necessária</p>
        )}
      </div>

      {/* Detalhamento do Resultado Líquido */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Apuração de Resultado (até hoje)</h3>
        
        <div className="space-y-3">
          {/* Receitas */}
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-sm text-gray-600">Receitas Realizadas</span>
            </div>
            <span className="text-sm font-semibold text-green-700">
              {formatCurrency(data.receitas ?? 0)}
            </span>
          </div>

          {/* Despesas */}
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <div className="flex items-center space-x-2">
              <TrendingDown className="w-4 h-4 text-red-600" />
              <span className="text-sm text-gray-600">Despesas Realizadas</span>
            </div>
            <span className="text-sm font-semibold text-red-700">
              {formatCurrency(data.despesas ?? 0)}
            </span>
          </div>

          {/* Custos */}
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <div className="flex items-center space-x-2">
              <TrendingDown className="w-4 h-4 text-orange-600" />
              <span className="text-sm text-gray-600">Custos Realizados</span>
            </div>
            <span className="text-sm font-semibold text-orange-700">
              {formatCurrency(data.custos ?? 0)}
            </span>
          </div>

          {/* Resultado Líquido */}
          <div className={`flex items-center justify-between py-3 mt-3 rounded-lg px-3 ${isNegative ? 'bg-red-50' : 'bg-green-50'}`}>
            <span className={`text-sm font-semibold ${isNegative ? 'text-red-800' : 'text-green-800'}`}>
              Resultado Líquido
            </span>
            <span className={`text-lg font-bold ${isNegative ? 'text-red-700' : 'text-green-700'}`}>
              {formatCurrency(saldoConsolidado)}
            </span>
          </div>

          {/* Saldo Inicial (se houver) */}
          {(data.saldo_inicial ?? 0) !== 0 && (
            <div className="flex items-center justify-between py-2 mt-2 text-xs text-gray-500">
              <span>Saldo Inicial do Exercício</span>
              <span>{formatCurrency(data.saldo_inicial ?? 0)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CashAvailabilityCards;







