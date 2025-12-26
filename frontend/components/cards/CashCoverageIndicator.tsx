import React from 'react';
import { Shield, AlertTriangle, CheckCircle } from 'lucide-react';
import type { OperationalAvailability, PayablesSummary } from '../../lib/api/finance';

interface CashCoverageIndicatorProps {
  availability: OperationalAvailability;
  payables: PayablesSummary;
}

type CoverageStatus = 'good' | 'warning' | 'risk';

const CashCoverageIndicator: React.FC<CashCoverageIndicatorProps> = ({ availability, payables }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  // Calcular cobertura: saldo disponível ÷ saídas previstas dos próximos 30 dias
  const availableCash = availability.total;
  const projectedOutflows = payables.next_30_days;
  
  // Se não houver saídas previstas, considerar cobertura infinita (boa)
  const coverageRatio = projectedOutflows > 0 
    ? availableCash / projectedOutflows 
    : 999; // Valor alto para indicar boa cobertura

  // Determinar status
  let status: CoverageStatus;
  let statusColor: string;
  let statusBg: string;
  let statusBorder: string;
  let statusIcon: React.ReactNode;
  let statusLabel: string;
  let statusMessage: string;

  if (coverageRatio >= 1.5) {
    // Cobertura >= 1.5 meses = boa
    status = 'good';
    statusColor = 'text-green-700';
    statusBg = 'bg-green-50';
    statusBorder = 'border-green-500';
    statusIcon = <CheckCircle className="w-8 h-8 text-green-600" />;
    statusLabel = '🟢 Cobertura Adequada';
    statusMessage = 'Caixa cobre bem as saídas previstas';
  } else if (coverageRatio >= 0.5) {
    // Cobertura entre 0.5 e 1.5 meses = atenção
    status = 'warning';
    statusColor = 'text-yellow-700';
    statusBg = 'bg-yellow-50';
    statusBorder = 'border-yellow-500';
    statusIcon = <AlertTriangle className="w-8 h-8 text-yellow-600" />;
    statusLabel = '🟡 Atenção';
    statusMessage = 'Cobertura abaixo do ideal - monitorar de perto';
  } else {
    // Cobertura < 0.5 meses = risco
    status = 'risk';
    statusColor = 'text-red-700';
    statusBg = 'bg-red-50';
    statusBorder = 'border-red-500';
    statusIcon = <Shield className="w-8 h-8 text-red-600" />;
    statusLabel = '🔴 Risco';
    statusMessage = 'Cobertura insuficiente - ação imediata necessária';
  }

  // Formatar ratio para exibição
  const formatRatio = () => {
    if (coverageRatio >= 999) {
      return '∞';
    }
    return coverageRatio.toFixed(1);
  };

  return (
    <div className="mb-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Cobertura de Caixa</h2>
      <div className={`bg-white rounded-lg shadow-md p-6 border-l-4 ${statusBorder}`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-3">
              {statusIcon}
              <div>
                <h3 className={`text-lg font-bold ${statusColor}`}>{statusLabel}</h3>
                <p className="text-sm text-gray-600 mt-1">{statusMessage}</p>
              </div>
            </div>
            
            <div className={`${statusBg} rounded-lg p-4 mt-4`}>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600 mb-1">Saldo Disponível</p>
                  <p className={`text-xl font-bold ${statusColor}`}>
                    {formatCurrency(availableCash)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600 mb-1">Saídas Previstas (30 dias)</p>
                  <p className="text-xl font-bold text-gray-800">
                    {formatCurrency(projectedOutflows)}
                  </p>
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">
                    Razão de Cobertura:
                  </span>
                  <span className={`text-2xl font-extrabold ${statusColor}`}>
                    {formatRatio()}x
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {coverageRatio >= 999 
                    ? 'Sem saídas previstas nos próximos 30 dias'
                    : `O caixa cobre ${formatRatio()} ${coverageRatio === 1 ? 'mês' : 'meses'} de saídas previstas`
                  }
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CashCoverageIndicator;

