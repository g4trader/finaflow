import React from 'react';
import { motion } from 'framer-motion';
import { Info, ChevronRight } from 'lucide-react';
import type { AnnualSummaryResponse } from '../../types/dashboard';

interface AnnualMonthlyTableProps {
  data: AnnualSummaryResponse;
  isLoading?: boolean;
  onMonthClick?: (params: { year: number; month: number }) => void;
}

const AnnualMonthlyTable: React.FC<AnnualMonthlyTableProps> = ({ 
  data, 
  isLoading = false,
  onMonthClick 
}) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const months = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
      >
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-48 mb-6"></div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {['Mês', 'Receita', 'Despesa', 'Custo'].map((header) => (
                    <th key={header} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <div className="h-4 bg-gray-200 rounded w-16"></div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Array.from({ length: 13 }).map((_, index) => (
                  <tr key={index}>
                    {Array.from({ length: 4 }).map((_, cellIndex) => (
                      <td key={cellIndex} className="px-6 py-4 whitespace-nowrap">
                        <div className="h-4 bg-gray-200 rounded w-20"></div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </motion.div>
    );
  }

  const getBalanceColor = (value: number) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getBalanceBgColor = (value: number) => {
    if (value > 0) return 'bg-green-50';
    if (value < 0) return 'bg-red-50';
    return 'bg-gray-50';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="featured-table-container bg-white rounded-lg shadow-sm border border-gray-200 p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Resumo Mensal - {data.year}
        </h3>
        {data.metadata && (
          <div className="group relative">
            <Info className="w-5 h-5 text-gray-400 hover:text-gray-600 cursor-help" />
            <div className="absolute right-0 top-6 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
              <p className="font-semibold mb-2">Fórmulas de Cálculo:</p>
              <p className="mb-1"><strong>Saldo Mensal:</strong> {data.metadata.saldo_formula}</p>
              <p className="mb-1"><strong>Saldo Acumulado:</strong> {data.metadata.saldo_acumulado_formula}</p>
              <p className="text-gray-300 mt-2">{data.metadata.saldo_acumulado_explanation}</p>
            </div>
          </div>
        )}
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Mês
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Receita
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Despesa
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Custo
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Saldo Mensal
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Saldo Acumulado
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.monthly.map((month, index) => (
              <motion.tr
                key={month.month}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`transition-colors duration-150 ${
                  onMonthClick ? 'hover:bg-gray-50 cursor-pointer' : 'hover:bg-gray-50'
                }`}
                onClick={() => onMonthClick?.({ year: data.year, month: month.month })}
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  <div className="flex items-center space-x-2">
                    <span>{months[month.month - 1]}</span>
                    {onMonthClick && (
                      <ChevronRight className="w-4 h-4 text-gray-400" />
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                  {formatCurrency(month.revenue)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                  {formatCurrency(month.expense)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-orange-600">
                  {formatCurrency(month.cost)}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${getBalanceColor(month.balance)}`}>
                  {formatCurrency(month.balance)}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm font-bold ${getBalanceColor(month.accumulated_balance)} ${getBalanceBgColor(month.accumulated_balance)}`}>
                  {formatCurrency(month.accumulated_balance)}
                </td>
              </motion.tr>
            ))}
          </tbody>
          <tfoot className="bg-gray-50">
            <tr className="font-semibold">
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                Total Anual
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                {formatCurrency(data.totals.revenue)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                {formatCurrency(data.totals.expense)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-orange-600">
                {formatCurrency(data.totals.cost)}
              </td>
              <td className={`px-6 py-4 whitespace-nowrap text-sm ${getBalanceColor(data.totals.balance)}`}>
                {formatCurrency(data.totals.balance)}
              </td>
              <td className={`px-6 py-4 whitespace-nowrap text-sm font-bold ${getBalanceColor(data.monthly[data.monthly.length - 1]?.accumulated_balance || 0)}`}>
                {formatCurrency(data.monthly[data.monthly.length - 1]?.accumulated_balance || 0)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </motion.div>
  );
};

export default AnnualMonthlyTable;
