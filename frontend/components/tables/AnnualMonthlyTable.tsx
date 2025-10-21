import React from 'react';
import { motion } from 'framer-motion';
import type { AnnualSummaryResponse } from '../../types/dashboard';

interface AnnualMonthlyTableProps {
  data: AnnualSummaryResponse;
  isLoading?: boolean;
}

const AnnualMonthlyTable: React.FC<AnnualMonthlyTableProps> = ({ data, isLoading = false }) => {
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
                  {['Mês', 'Receita', 'Despesa', 'Custo', 'Caixa Final'].map((header) => (
                    <th key={header} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <div className="h-4 bg-gray-200 rounded w-16"></div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Array.from({ length: 13 }).map((_, index) => (
                  <tr key={index}>
                    {Array.from({ length: 5 }).map((_, cellIndex) => (
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

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="featured-table-container bg-white rounded-lg shadow-sm border border-gray-200 p-6"
    >
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        Resumo Mensal - {data.year}
      </h3>
      
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
                      Caixa Final
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
                className="hover:bg-gray-50 transition-colors duration-150"
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {months[month.month - 1]}
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
                <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                  month.caixa_final >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(month.caixa_final)}
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
              <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                data.totals.balance >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(data.totals.balance)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </motion.div>
  );
};

export default AnnualMonthlyTable;
