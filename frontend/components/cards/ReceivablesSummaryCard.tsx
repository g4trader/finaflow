import React from 'react';
import { Calendar, AlertCircle, Clock, CalendarDays } from 'lucide-react';
import type { ReceivablesSummary } from '../../lib/api/finance';

interface ReceivablesSummaryCardProps {
  data: ReceivablesSummary;
  onViewDetails?: () => void;
}

// Componente helper para exibir valores monetários sem quebrar linha
const ValueDisplay: React.FC<{ value: number; isHighlighted: boolean; colorClass: string }> = ({
  value,
  isHighlighted,
  colorClass,
}) => {
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(val);
  };

  // Ajustar tamanho da fonte para valores muito grandes
  const getFontSize = () => {
    const absValue = Math.abs(value);
    if (absValue >= 1000000) {
      return 'text-lg sm:text-xl';
    }
    return 'text-xl';
  };

  return (
    <p
      className={`${getFontSize()} font-bold ${colorClass} whitespace-nowrap tabular-nums`}
      style={{ fontVariantNumeric: 'tabular-nums' }}
    >
      {formatCurrency(value)}
    </p>
  );
};

// Componente de card individual padronizado
interface SummaryCardItemProps {
  icon: React.ReactNode;
  title: string;
  value: number;
  isActive: boolean;
  colorConfig: {
    active: {
      bg: string;
      border: string;
      icon: string;
      title: string;
      value: string;
    };
    inactive: {
      bg: string;
      border: string;
      icon: string;
      title: string;
      value: string;
    };
  };
}

const SummaryCardItem: React.FC<SummaryCardItemProps> = ({
  icon,
  title,
  value,
  isActive,
  colorConfig,
}) => {
  const config = isActive ? colorConfig.active : colorConfig.inactive;

  return (
    <div
      className={`p-4 rounded-lg border-l-4 ${config.bg} ${config.border} h-full flex flex-col`}
      style={{ minHeight: '120px' }}
    >
      {/* Ícone + Título (linha única, discreta) */}
      <div className="flex items-center space-x-2 mb-3">
        <div className={config.icon}>{icon}</div>
        <span className={`text-xs font-medium ${config.title} truncate`}>{title}</span>
      </div>

      {/* Valor principal (destaque máximo) */}
      <div className="flex-1 flex items-start">
        <ValueDisplay value={value} isHighlighted={isActive} colorClass={config.value} />
      </div>
    </div>
  );
};

const ReceivablesSummaryCard: React.FC<ReceivablesSummaryCardProps> = ({ data, onViewDetails }) => {
  return (
    <div className="mb-6 h-full flex flex-col">
      {/* Título do bloco */}
      <h2 className="text-xl font-bold mb-4 text-gray-800">Posição de Contas a Receber</h2>

      {/* Container dos cards */}
      <div className="bg-white rounded-lg shadow-md p-6 flex-1">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Vencido */}
          <SummaryCardItem
            icon={<AlertCircle className="w-4 h-4" />}
            title="Vencido"
            value={data.overdue}
            isActive={data.overdue > 0}
            colorConfig={{
              active: {
                bg: 'bg-yellow-50/80',
                border: 'border-yellow-500',
                icon: 'text-yellow-500',
                title: 'text-yellow-800',
                value: 'text-yellow-600',
              },
              inactive: {
                bg: 'bg-gray-50',
                border: 'border-gray-300',
                icon: 'text-gray-400',
                title: 'text-gray-600',
                value: 'text-gray-500',
              },
            }}
          />

          {/* Vence hoje */}
          <SummaryCardItem
            icon={<Clock className="w-4 h-4" />}
            title="A Receber Hoje"
            value={data.due_today}
            isActive={data.due_today > 0}
            colorConfig={{
              active: {
                bg: 'bg-green-50/80',
                border: 'border-green-500',
                icon: 'text-green-500',
                title: 'text-green-800',
                value: 'text-green-600',
              },
              inactive: {
                bg: 'bg-gray-50',
                border: 'border-gray-300',
                icon: 'text-gray-400',
                title: 'text-gray-600',
                value: 'text-gray-500',
              },
            }}
          />

          {/* Próximos 7 dias */}
          <SummaryCardItem
            icon={<Calendar className="w-4 h-4" />}
            title="Próximos 7 dias"
            value={data.next_7_days}
            isActive={true}
            colorConfig={{
              active: {
                bg: 'bg-blue-50',
                border: 'border-blue-300',
                icon: 'text-blue-500',
                title: 'text-blue-800',
                value: 'text-blue-600',
              },
              inactive: {
                bg: 'bg-gray-50',
                border: 'border-gray-300',
                icon: 'text-gray-400',
                title: 'text-gray-600',
                value: 'text-gray-500',
              },
            }}
          />

          {/* Próximos 30 dias */}
          <SummaryCardItem
            icon={<CalendarDays className="w-4 h-4" />}
            title="Próximos 30 dias"
            value={data.next_30_days}
            isActive={true}
            colorConfig={{
              active: {
                bg: 'bg-indigo-50',
                border: 'border-indigo-300',
                icon: 'text-indigo-500',
                title: 'text-indigo-800',
                value: 'text-indigo-600',
              },
              inactive: {
                bg: 'bg-gray-50',
                border: 'border-gray-300',
                icon: 'text-gray-400',
                title: 'text-gray-600',
                value: 'text-gray-500',
              },
            }}
          />
        </div>

        {/* Botão de detalhes (se houver vencidos) */}
        {data.overdue > 0 && onViewDetails && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <button
              onClick={onViewDetails}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
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
