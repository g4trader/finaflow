import React from 'react';
import { AlertCircle, AlertTriangle, TrendingDown, CheckCircle } from 'lucide-react';
import type { OperationalAlerts } from '../../lib/api/finance';

interface FinancialAlertsProps {
  data: OperationalAlerts;
  onAlertClick?: (type: string) => void;
}

const FinancialAlerts: React.FC<FinancialAlertsProps> = ({ data, onAlertClick }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const hasAlerts = 
    data.overdue_payables.count > 0 ||
    data.overdue_receivables.count > 0 ||
    data.negative_cash_forecast.has_alert;

  if (!hasAlerts) {
    return (
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4 text-gray-800">Alertas Financeiros Rápidos</h2>
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 flex items-center space-x-3">
          <CheckCircle className="w-6 h-6 text-green-500" />
          <div>
            <p className="text-green-800 font-medium">Tudo em dia</p>
            <p className="text-sm text-green-600">Nenhum alerta financeiro no momento</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Alertas Financeiros Rápidos</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Contas vencidas a pagar */}
        {data.overdue_payables.count > 0 && (
          <div
            className="bg-red-50 border border-red-200 rounded-lg p-4 cursor-pointer hover:bg-red-100 transition-colors"
            onClick={() => onAlertClick?.('overdue_payables')}
          >
            <div className="flex items-center space-x-3 mb-2">
              <AlertCircle className="w-6 h-6 text-red-500" />
              <span className="text-sm font-medium text-red-800">Contas Vencidas a Pagar</span>
            </div>
            <p className="text-lg font-bold text-red-600">{data.overdue_payables.count} conta(s)</p>
            <p className="text-sm text-red-700">{formatCurrency(data.overdue_payables.value)}</p>
          </div>
        )}

        {/* Contas vencidas a receber */}
        {data.overdue_receivables.count > 0 && (
          <div
            className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 cursor-pointer hover:bg-yellow-100 transition-colors"
            onClick={() => onAlertClick?.('overdue_receivables')}
          >
            <div className="flex items-center space-x-3 mb-2">
              <AlertTriangle className="w-6 h-6 text-yellow-500" />
              <span className="text-sm font-medium text-yellow-800">Contas Vencidas a Receber</span>
            </div>
            <p className="text-lg font-bold text-yellow-600">{data.overdue_receivables.count} conta(s)</p>
            <p className="text-sm text-yellow-700">{formatCurrency(data.overdue_receivables.value)}</p>
          </div>
        )}

        {/* Projeção negativa de caixa */}
        {data.negative_cash_forecast.has_alert && (
          <div
            className="bg-red-50 border border-red-200 rounded-lg p-4 cursor-pointer hover:bg-red-100 transition-colors"
            onClick={() => onAlertClick?.('negative_forecast')}
          >
            <div className="flex items-center space-x-3 mb-2">
              <TrendingDown className="w-6 h-6 text-red-500" />
              <span className="text-sm font-medium text-red-800">Projeção Negativa de Caixa</span>
            </div>
            <p className="text-sm text-red-700">Saldo projetado: {formatCurrency(data.negative_cash_forecast.projected_balance)}</p>
            <p className="text-xs text-red-600 mt-1">Próximos 30 dias</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FinancialAlerts;

