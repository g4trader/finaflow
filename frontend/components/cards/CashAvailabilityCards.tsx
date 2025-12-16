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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Bancos */}
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Banknote className="w-6 h-6 text-blue-500" />
              <span className="text-sm font-medium text-gray-600">Bancos</span>
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-800">{formatCurrency(data.banks)}</p>
        </div>

        {/* Caixa */}
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Wallet className="w-6 h-6 text-green-500" />
              <span className="text-sm font-medium text-gray-600">Caixa / Dinheiro</span>
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-800">{formatCurrency(data.cash)}</p>
        </div>

        {/* Investimentos */}
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-6 h-6 text-purple-500" />
              <span className="text-sm font-medium text-gray-600">Aplicações / Investimentos</span>
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-800">{formatCurrency(data.investments)}</p>
        </div>

        {/* Total */}
        <div className={`bg-white rounded-lg shadow-md p-6 border-l-4 ${isNegative ? 'border-red-500' : 'border-indigo-500'}`}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <DollarSign className={`w-6 h-6 ${isNegative ? 'text-red-500' : 'text-indigo-500'}`} />
              <span className="text-sm font-medium text-gray-600">Total Disponível</span>
            </div>
          </div>
          <p className={`text-2xl font-bold ${isNegative ? 'text-red-600' : 'text-gray-800'}`}>
            {formatCurrency(data.total)}
          </p>
          {isNegative && (
            <p className="text-xs text-red-600 mt-1">⚠️ Saldo negativo</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default CashAvailabilityCards;

