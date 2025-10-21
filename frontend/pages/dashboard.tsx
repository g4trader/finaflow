import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp, TrendingDown, DollarSign, Users, CreditCard,
  BarChart3, Calendar, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import Layout from '../components/layout/Layout';
import { useAuth } from '../context/AuthContext';
import api, { getCashFlow, getTransactions } from '../services/api';

interface CashFlowData {
  date: string;
  opening_balance: number;
  total_revenue: number;
  total_expenses: number;
  total_costs: number;
  net_flow: number;
  closing_balance: number;
}

interface AnnualData {
  year: number;
  annual_totals: {
    receita: number;
    despesa: number;
    custo: number;
    saldo: number;
  };
  monthly_breakdown: Array<{
    mes: number;
    mes_nome: string;
    receita: number;
    despesa: number;
    custo: number;
    saldo: number;
  }>;
}

interface TransactionData {
  id: string;
  description: string;
  amount: number;
  transaction_type: string;
  transaction_date: string;
  category: string;
}

const Dashboard = () => {
  const { user, needsBusinessUnitSelection } = useAuth();
  const [cashFlowData, setCashFlowData] = useState<CashFlowData[]>([]);
  const [recentTransactions, setRecentTransactions] = useState<TransactionData[]>([]);
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState({
    totalRevenue: 0,
    totalExpenses: 0,
    totalCosts: 0,
    netFlow: 0,
    currentBalance: 0,
    transactionCount: 0
  });
  const [saldoDisponivel, setSaldoDisponivel] = useState({
    total_geral: 0,
    contas_bancarias: { total: 0, detalhes: [] },
    caixas: { total: 0, detalhes: [] },
    investimentos: { total: 0, detalhes: [] }
  });
  const [annualData, setAnnualData] = useState<AnnualData | null>(null);
  const [selectedYear, setSelectedYear] = useState(2025);

  useEffect(() => {
    // Se o usuário precisa selecionar uma BU, redirecionar
    if (needsBusinessUnitSelection) {
      window.location.href = '/select-business-unit';
      return;
    }
    
    // Se não tem BU selecionada, redirecionar
    if (!user?.business_unit_id) {
      window.location.href = '/select-business-unit';
      return;
    }

    loadDashboardData();
  }, [needsBusinessUnitSelection, user]);

  useEffect(() => {
    if (selectedYear) {
      loadDashboardData();
    }
  }, [selectedYear]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      const [annualResponse, saldoResponse] = await Promise.all([
        api.get(`/financial/cash-flow-annual?year=${selectedYear}`).then(r => r.data),
        api.get('/saldo-disponivel').then(r => r.data).catch(() => ({ saldo_disponivel: { total_geral: 0, contas_bancarias: { total: 0, detalhes: [] }, caixas: { total: 0, detalhes: [] }, investimentos: { total: 0, detalhes: [] } } }))
      ]);

      setAnnualData(annualResponse);
      setSaldoDisponivel(saldoResponse.saldo_disponivel || saldoResponse);

      // Usar dados anuais para as métricas
      if (annualResponse && annualResponse.annual_totals) {
        const { receita, despesa, custo, saldo } = annualResponse.annual_totals;
        
        setMetrics({
          totalRevenue: receita,
          totalExpenses: despesa,
          totalCosts: custo,
          netFlow: saldo,
          currentBalance: saldo,
          transactionCount: annualResponse.monthly_breakdown.reduce((sum, month) => 
            sum + (month.receita > 0 ? 1 : 0) + (month.despesa > 0 ? 1 : 0) + (month.custo > 0 ? 1 : 0), 0)
        });
      }

    } catch (error) {
      console.error('Erro ao carregar dados do dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const getMetricIcon = (type: string) => {
    switch (type) {
      case 'revenue':
        return <TrendingUp className="w-6 h-6 text-green-600" />;
      case 'expenses':
        return <TrendingDown className="w-6 h-6 text-red-600" />;
      case 'costs':
        return <DollarSign className="w-6 h-6 text-orange-600" />;
      case 'balance':
        return <CreditCard className="w-6 h-6 text-blue-600" />;
      default:
        return <BarChart3 className="w-6 h-6 text-gray-600" />;
    }
  };

  const getMetricColor = (type: string) => {
    switch (type) {
      case 'revenue':
        return 'text-green-600 bg-green-50';
      case 'expenses':
        return 'text-red-600 bg-red-50';
      case 'costs':
        return 'text-orange-600 bg-orange-50';
      case 'balance':
        return 'text-blue-600 bg-blue-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading) {
    return (
      <Layout title="Dashboard">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Dashboard">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Olá, {user?.first_name || 'Usuário'}!
            </h1>
            <p className="text-gray-600">
              Bem-vindo ao seu dashboard financeiro
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <select 
              value={selectedYear} 
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={2024}>2024</option>
              <option value={2025}>2025</option>
            </select>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Calendar className="w-4 h-4" />
              <span>{new Date().toLocaleDateString('pt-BR')}</span>
            </div>
          </div>
        </div>

        {/* Métricas Principais */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          >
                <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Receita Total</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(metrics.totalRevenue)}
                </p>
              </div>
              {getMetricIcon('revenue')}
            </div>
            <div className="mt-4 flex items-center text-sm">
              <ArrowUpRight className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-green-600 font-medium">+12.5%</span>
              <span className="text-gray-500 ml-1">vs mês anterior</span>
                </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          >
                <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Despesas Totais</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(metrics.totalExpenses)}
                </p>
              </div>
              {getMetricIcon('expenses')}
            </div>
            <div className="mt-4 flex items-center text-sm">
              <ArrowDownRight className="w-4 h-4 text-red-600 mr-1" />
              <span className="text-red-600 font-medium">+8.2%</span>
              <span className="text-gray-500 ml-1">vs mês anterior</span>
                </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Custos Totais</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(metrics.totalCosts)}
                </p>
              </div>
              {getMetricIcon('costs')}
            </div>
            <div className="mt-4 flex items-center text-sm">
              <ArrowDownRight className="w-4 h-4 text-orange-600 mr-1" />
              <span className="text-orange-600 font-medium">+5.7%</span>
              <span className="text-gray-500 ml-1">vs mês anterior</span>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          >
                <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Saldo Atual</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(metrics.currentBalance)}
                </p>
              </div>
              {getMetricIcon('balance')}
            </div>
            <div className="mt-4 flex items-center text-sm">
              <ArrowUpRight className="w-4 h-4 text-blue-600 mr-1" />
              <span className="text-blue-600 font-medium">+15.3%</span>
              <span className="text-gray-500 ml-1">vs mês anterior</span>
            </div>
          </motion.div>
        </div>

        {/* Saldo Disponível */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg border border-purple-700 p-6 text-white"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">💰 Saldo Disponível</h3>
            <span className="text-3xl font-bold">{formatCurrency(saldoDisponivel.total_geral)}</span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white bg-opacity-20 rounded-lg p-4">
              <p className="text-purple-100 text-sm mb-1">Contas Bancárias</p>
              <p className="text-2xl font-bold">{formatCurrency(saldoDisponivel.contas_bancarias?.total || 0)}</p>
              {saldoDisponivel.contas_bancarias?.detalhes && saldoDisponivel.contas_bancarias.detalhes.length > 0 && (
                <div className="mt-2 space-y-1">
                  {saldoDisponivel.contas_bancarias.detalhes.slice(0, 3).map((conta: any, idx: number) => (
                    <div key={idx} className="text-xs text-purple-100 flex justify-between">
                      <span>{conta.banco}</span>
                      <span>{formatCurrency(conta.saldo)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-white bg-opacity-20 rounded-lg p-4">
              <p className="text-purple-100 text-sm mb-1">Caixa / Dinheiro</p>
              <p className="text-2xl font-bold">{formatCurrency(saldoDisponivel.caixas?.total || 0)}</p>
              {saldoDisponivel.caixas?.detalhes && saldoDisponivel.caixas.detalhes.length > 0 && (
                <div className="mt-2 space-y-1">
                  {saldoDisponivel.caixas.detalhes.slice(0, 3).map((caixa: any, idx: number) => (
                    <div key={idx} className="text-xs text-purple-100 flex justify-between">
                      <span>{caixa.nome}</span>
                      <span>{formatCurrency(caixa.saldo)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-white bg-opacity-20 rounded-lg p-4">
              <p className="text-purple-100 text-sm mb-1">Investimentos</p>
              <p className="text-2xl font-bold">{formatCurrency(saldoDisponivel.investimentos?.total || 0)}</p>
              {saldoDisponivel.investimentos?.detalhes && saldoDisponivel.investimentos.detalhes.length > 0 && (
                <div className="mt-2 space-y-1">
                  {saldoDisponivel.investimentos.detalhes.slice(0, 3).map((inv: any, idx: number) => (
                    <div key={idx} className="text-xs text-purple-100 flex justify-between">
                      <span>{inv.tipo}</span>
                      <span>{formatCurrency(inv.valor)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </motion.div>

        {/* Breakdown Mensal */}
        {annualData && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-6">
              Evolução Mensal - {selectedYear}
            </h3>
            
            {/* Gráfico de Linhas */}
            <div className="h-64 mb-6">
              <div className="flex items-end justify-between space-x-2 h-full">
                {annualData.monthly_breakdown.map((month) => {
                  const maxValue = Math.max(
                    ...annualData.monthly_breakdown.map(m => Math.max(m.receita, m.despesa, m.custo))
                  );
                  return (
                    <div key={month.mes} className="flex-1 flex flex-col items-center space-y-1">
                      <div className="w-full flex flex-col space-y-1 h-48">
                        {/* Receita */}
                        <div className="w-full bg-gray-200 rounded-sm">
                          <div 
                            className="bg-green-500 rounded-sm"
                            style={{ height: `${(month.receita / maxValue) * 100}%` }}
                          ></div>
                        </div>
                        {/* Despesa */}
                        <div className="w-full bg-gray-200 rounded-sm">
                          <div 
                            className="bg-red-500 rounded-sm"
                            style={{ height: `${(month.despesa / maxValue) * 100}%` }}
                          ></div>
                        </div>
                        {/* Custo */}
                        <div className="w-full bg-gray-200 rounded-sm">
                          <div 
                            className="bg-orange-500 rounded-sm"
                            style={{ height: `${(month.custo / maxValue) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                      <span className="text-xs text-gray-500 mt-2">
                        {month.mes_nome.substring(0, 3)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Legenda */}
            <div className="flex items-center justify-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span>Receitas</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span>Despesas</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                <span>Custos</span>
              </div>
            </div>
          </motion.div>
        )}

        {/* Tabela Mensal Detalhada */}
        {annualData && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-6">
              Resumo Mensal - {selectedYear}
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
                      Saldo
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {annualData.monthly_breakdown.map((month) => (
                    <tr key={month.mes} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {month.mes_nome}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                        {formatCurrency(month.receita)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                        {formatCurrency(month.despesa)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-orange-600">
                        {formatCurrency(month.custo)}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                        month.saldo >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {formatCurrency(month.saldo)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-gray-50">
                  <tr className="font-semibold">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      Total Anual
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                      {formatCurrency(annualData.annual_totals.receita)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                      {formatCurrency(annualData.annual_totals.despesa)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-orange-600">
                      {formatCurrency(annualData.annual_totals.custo)}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                      annualData.annual_totals.saldo >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(annualData.annual_totals.saldo)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </motion.div>
        )}

        {/* Transações Recentes */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Transações Recentes</h3>
            <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
              Ver todas
            </button>
          </div>
          
          <div className="space-y-4">
            {recentTransactions.map((transaction) => (
              <div key={transaction.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    transaction.transaction_type === 'credit' ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    {transaction.transaction_type === 'credit' ? (
                      <ArrowUpRight className="w-5 h-5 text-green-600" />
                    ) : (
                      <ArrowDownRight className="w-5 h-5 text-red-600" />
                            )}
                          </div>
                  <div>
                    <p className="font-medium text-gray-900">{transaction.description}</p>
                    <p className="text-sm text-gray-500">{transaction.category}</p>
                          </div>
                        </div>
                        <div className="text-right">
                  <p className={`font-semibold ${
                    transaction.transaction_type === 'credit' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {transaction.transaction_type === 'credit' ? '+' : '-'}
                    {formatCurrency(transaction.amount)}
                  </p>
                  <p className="text-sm text-gray-500">{formatDate(transaction.transaction_date)}</p>
                      </div>
                    </div>
                  ))}
                </div>
          </motion.div>
      </div>
    </Layout>
  );
};

export default Dashboard;

