import React from 'react';
import { Banknote, Wallet, TrendingUp, DollarSign } from 'lucide-react';
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

  return (
    <div className="mb-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Composição das Disponibilidades de Caixa</h2>
      
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

      {/* Composição Secundária */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Bancos */}
        <div className="bg-white rounded-lg shadow-md p-5 border-l-4 border-blue-500">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Banknote className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-medium text-gray-600">Bancos</span>
            </div>
          </div>
          <p className="text-xl font-bold text-gray-800">{formatCurrency(data.banks)}</p>
        </div>

        {/* Caixa */}
        <div className="bg-white rounded-lg shadow-md p-5 border-l-4 border-green-500">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Wallet className="w-5 h-5 text-green-500" />
              <span className="text-sm font-medium text-gray-600">Caixa / Dinheiro</span>
            </div>
          </div>
          <p className="text-xl font-bold text-gray-800">{formatCurrency(data.cash)}</p>
        </div>

        {/* Investimentos */}
        <div className="bg-white rounded-lg shadow-md p-5 border-l-4 border-purple-500">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-purple-500" />
              <span className="text-sm font-medium text-gray-600">Aplicações / Investimentos</span>
            </div>
          </div>
          <p className="text-xl font-bold text-gray-800">{formatCurrency(data.investments)}</p>
        </div>
      </div>
    </div>
  );
};

export default CashAvailabilityCards;







