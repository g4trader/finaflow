import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import Modal from '../ui/Modal';
import { fetchMonthlyDailySummary, fetchMonthlyTransactions } from '../../lib/api/finance';
import type { MonthlyDailySummaryResponse, MonthlyTransactionsResponse } from '../../types/dashboard';

interface MonthlyDrilldownModalProps {
  isOpen: boolean;
  onClose: () => void;
  year: number;
  month: number;
}

const MonthlyDrilldownModal: React.FC<MonthlyDrilldownModalProps> = ({
  isOpen,
  onClose,
  year,
  month,
}) => {
  const [dailySummary, setDailySummary] = useState<MonthlyDailySummaryResponse | null>(null);
  const [transactions, setTransactions] = useState<MonthlyTransactionsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Filtros e paginação
  const [transactionType, setTransactionType] = useState<string>('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 50;

  const months = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];

  // Carregar dados quando o modal abrir ou filtros mudarem
  useEffect(() => {
    if (isOpen) {
      loadData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, year, month, transactionType, currentPage]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Carregar em paralelo
      const [dailyData, transactionsData] = await Promise.all([
        fetchMonthlyDailySummary(year, month),
        fetchMonthlyTransactions({
          year,
          month,
          type: transactionType !== 'ALL' ? transactionType as "RECEITA" | "DESPESA" | "CUSTO" : undefined,
          page: currentPage,
          page_size: pageSize,
        }),
      ]);

      setDailySummary(dailyData);
      setTransactions(transactionsData);
    } catch (err) {
      console.error('Erro ao carregar dados do drill down:', err);
      setError('Erro ao carregar dados. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: string | number) => {
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(numValue);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
    });
  };

  const formatDateFull = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  const getBalanceColor = (value: string | number) => {
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    if (numValue > 0) return 'text-green-600';
    if (numValue < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'RECEITA':
        return 'text-green-600';
      case 'DESPESA':
        return 'text-red-600';
      case 'CUSTO':
        return 'text-orange-600';
      default:
        return 'text-gray-600';
    }
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && transactions && newPage <= transactions.total_pages) {
      setCurrentPage(newPage);
    }
  };

  const handleTypeFilterChange = (newType: string) => {
    setTransactionType(newType);
    setCurrentPage(1); // Resetar para primeira página ao mudar filtro
  };

  if (!isOpen) return null;

  const modalTitle = `Detalhes de ${months[month - 1]} de ${year}`;
  const modalSubtitle = "Resumo diário e lançamentos financeiros";

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={modalTitle}
      size="xl"
    >
      <div className="space-y-6">
        {/* Subtítulo */}
        <p className="text-sm text-gray-600 mb-4">
          {modalSubtitle}
        </p>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Conteúdo */}
        {!loading && !error && dailySummary && transactions && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Seção 1: Resumo Diário */}
            <div className="space-y-4">
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">
                  Resumo Diário
                </h4>
                <p className="text-xs text-gray-500 mb-4">
                  Os totais deste mês batem com o dashboard anual
                </p>
              </div>

              <div className="overflow-x-auto border border-gray-200 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        Data
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        Receita
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        Despesa
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        Custo
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        Saldo
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {dailySummary.days.map((day) => {
                      const hasData = parseFloat(day.revenue) !== 0 || 
                                     parseFloat(day.expense) !== 0 || 
                                     parseFloat(day.cost) !== 0;
                      const isEmpty = !hasData;
                      
                      return (
                        <tr 
                          key={day.day} 
                          className={`hover:bg-gray-50 ${isEmpty ? 'opacity-60' : ''}`}
                        >
                          <td className="px-4 py-2 text-sm text-gray-900">
                            {formatDate(day.date)}
                          </td>
                          <td className={`px-4 py-2 text-sm ${hasData ? 'text-green-600' : 'text-gray-400'}`}>
                            {formatCurrency(day.revenue)}
                          </td>
                          <td className={`px-4 py-2 text-sm ${hasData ? 'text-red-600' : 'text-gray-400'}`}>
                            {formatCurrency(day.expense)}
                          </td>
                          <td className={`px-4 py-2 text-sm ${hasData ? 'text-orange-600' : 'text-gray-400'}`}>
                            {formatCurrency(day.cost)}
                          </td>
                          <td className={`px-4 py-2 text-sm font-medium ${getBalanceColor(day.balance)}`}>
                            {formatCurrency(day.balance)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot className="bg-gray-50">
                    <tr className="font-semibold">
                      <td className="px-4 py-2 text-sm text-gray-900">
                        Total do mês
                      </td>
                      <td className="px-4 py-2 text-sm text-green-600">
                        {formatCurrency(dailySummary.metadata.month_total_revenue)}
                      </td>
                      <td className="px-4 py-2 text-sm text-red-600">
                        {formatCurrency(dailySummary.metadata.month_total_expense)}
                      </td>
                      <td className="px-4 py-2 text-sm text-orange-600">
                        {formatCurrency(dailySummary.metadata.month_total_cost)}
                      </td>
                      <td className={`px-4 py-2 text-sm ${getBalanceColor(dailySummary.metadata.month_total_balance)}`}>
                        {formatCurrency(dailySummary.metadata.month_total_balance)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* Seção 2: Lançamentos */}
            <div className="space-y-4">
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-4">
                  Lançamentos do Mês
                </h4>

                {/* Filtros */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo
                  </label>
                  <select
                    value={transactionType}
                    onChange={(e) => handleTypeFilterChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="ALL">Todos</option>
                    <option value="RECEITA">Receita</option>
                    <option value="DESPESA">Despesa</option>
                    <option value="CUSTO">Custo</option>
                  </select>
                </div>

                {/* Resumo Filtrado */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                  <p className="text-xs font-medium text-blue-900 mb-1">
                    Resumo filtrado:
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-600">Receita:</span>{' '}
                      <span className="text-green-600 font-medium">
                        {formatCurrency(transactions.summary.revenue)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Despesa:</span>{' '}
                      <span className="text-red-600 font-medium">
                        {formatCurrency(transactions.summary.expense)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Custo:</span>{' '}
                      <span className="text-orange-600 font-medium">
                        {formatCurrency(transactions.summary.cost)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Saldo:</span>{' '}
                      <span className={`font-medium ${getBalanceColor(transactions.summary.balance)}`}>
                        {formatCurrency(transactions.summary.balance)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tabela de Lançamentos */}
              {transactions.items.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-gray-500">
                    Nenhum lançamento encontrado para este mês com os filtros atuais.
                  </p>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto border border-gray-200 rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Data
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Descrição
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Tipo
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Grupo
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Subgrupo
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Conta
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Valor
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {transactions.items.map((item) => (
                          <tr key={item.id} className="hover:bg-gray-50">
                            <td className="px-4 py-2 text-sm text-gray-900">
                              {formatDateFull(item.date)}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-900">
                              {item.description}
                            </td>
                            <td className={`px-4 py-2 text-sm font-medium ${getTypeColor(item.type)}`}>
                              {item.type}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {item.group || '-'}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {item.subgroup || '-'}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {item.account || '-'}
                            </td>
                            <td className={`px-4 py-2 text-sm font-medium ${getTypeColor(item.type)}`}>
                              {formatCurrency(item.amount)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Paginação */}
                  {transactions.total_pages > 1 && (
                    <div className="flex items-center justify-between border-t border-gray-200 pt-4">
                      <div className="text-sm text-gray-600">
                        Mostrando {((currentPage - 1) * pageSize) + 1}–
                        {Math.min(currentPage * pageSize, transactions.total_items)} de{' '}
                        {transactions.total_items} lançamentos
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handlePageChange(currentPage - 1)}
                          disabled={currentPage === 1}
                          className={`px-3 py-1 rounded-md text-sm ${
                            currentPage === 1
                              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          }`}
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <span className="text-sm text-gray-700">
                          Página {currentPage} de {transactions.total_pages}
                        </span>
                        <button
                          onClick={() => handlePageChange(currentPage + 1)}
                          disabled={currentPage === transactions.total_pages}
                          className={`px-3 py-1 rounded-md text-sm ${
                            currentPage === transactions.total_pages
                              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          }`}
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default MonthlyDrilldownModal;

