import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  CreditCard,
  Users,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  Filter,
  Wallet,
  Layers,
  FileText,
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { getAccounts, getTransactions, getGroups, getSubgroups } from '../services/api';

interface MetricCard {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
  color: string;
  loading?: boolean;
}

interface DashboardData {
  accounts: any[];
  transactions: any[];
  groups: any[];
  subgroups: any[];
}

export default function Dashboard() {
  const [timeRange, setTimeRange] = useState('30d');
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DashboardData>({
    accounts: [],
    transactions: [],
    groups: [],
    subgroups: []
  });
  const { token } = useAuth();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Buscar dados em paralelo
        const [accounts, transactions, groups, subgroups] = await Promise.all([
          getAccounts(token),
          getTransactions(token),
          getGroups(token),
          getSubgroups(token)
        ]);

        setData({
          accounts: accounts || [],
          transactions: transactions || [],
          groups: groups || [],
          subgroups: subgroups || []
        });
      } catch (error) {
        console.error('Erro ao carregar dados do dashboard:', error);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchDashboardData();
    }
  }, [token]);

  // Calcular métricas baseadas nos dados reais
  const totalAccounts = data.accounts.length;
  const totalTransactions = data.transactions.length;
  const totalGroups = data.groups.length;
  const totalSubgroups = data.subgroups.length;

  // Calcular valor total das transações
  const totalAmount = data.transactions.reduce((sum, transaction) => {
    return sum + (parseFloat(transaction.amount) || 0);
  }, 0);

  // Transações dos últimos 30 dias
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  
  const recentTransactions = data.transactions.filter(transaction => {
    const transactionDate = new Date(transaction.created_at);
    return transactionDate >= thirtyDaysAgo;
  });

  const recentAmount = recentTransactions.reduce((sum, transaction) => {
    return sum + (parseFloat(transaction.amount) || 0);
  }, 0);

  const metrics: MetricCard[] = [
    {
      title: 'Total de Contas',
      value: loading ? '...' : totalAccounts.toString(),
      change: '+2',
      changeType: 'positive',
      icon: <Wallet className="w-6 h-6" />,
      color: 'bg-blue-500',
      loading
    },
    {
      title: 'Total de Transações',
      value: loading ? '...' : totalTransactions.toString(),
      change: recentTransactions.length.toString(),
      changeType: 'positive',
      icon: <CreditCard className="w-6 h-6" />,
      color: 'bg-green-500',
      loading
    },
    {
      title: 'Valor Total',
      value: loading ? '...' : `R$ ${totalAmount.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
      change: `R$ ${recentAmount.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
      changeType: recentAmount > 0 ? 'positive' : 'neutral',
      icon: <DollarSign className="w-6 h-6" />,
      color: 'bg-purple-500',
      loading
    },
    {
      title: 'Grupos Ativos',
      value: loading ? '...' : totalGroups.toString(),
      change: totalSubgroups.toString(),
      changeType: 'positive',
      icon: <Layers className="w-6 h-6" />,
      color: 'bg-orange-500',
      loading
    },
  ];

  // Dados para gráficos
  const transactionData = recentTransactions.slice(-14).map((transaction, index) => ({
    day: (index + 1).toString(),
    amount: parseFloat(transaction.amount) || 0,
    date: new Date(transaction.created_at).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
  }));

  const accountData = data.accounts.slice(0, 5).map(account => ({
    name: account.name || 'Conta sem nome',
    balance: parseFloat(account.balance) || 0,
    color: `#${Math.floor(Math.random()*16777215).toString(16)}`
  }));

  const recentTransactionsList = data.transactions
    .slice(0, 5)
    .map(transaction => ({
      id: transaction.id,
      description: transaction.description || 'Transação sem descrição',
      amount: parseFloat(transaction.amount) || 0,
      type: parseFloat(transaction.amount) > 0 ? 'credit' : 'debit',
      date: transaction.created_at,
      status: 'completed',
    }));

  const MetricCard: React.FC<{ metric: MetricCard; index: number }> = ({ metric, index }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
    >
      <Card hover>
        <Card.Body className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500 mb-1">
                {metric.title}
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {metric.loading ? (
                  <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
                ) : (
                  metric.value
                )}
              </p>
              <div className="flex items-center mt-2">
                {metric.changeType === 'positive' ? (
                  <ArrowUpRight className="w-4 h-4 text-green-500 mr-1" />
                ) : metric.changeType === 'negative' ? (
                  <ArrowDownRight className="w-4 h-4 text-red-500 mr-1" />
                ) : (
                  <Activity className="w-4 h-4 text-gray-500 mr-1" />
                )}
                <span
                  className={`text-sm font-medium ${
                    metric.changeType === 'positive'
                      ? 'text-green-600'
                      : metric.changeType === 'negative'
                      ? 'text-red-600'
                      : 'text-gray-600'
                  }`}
                >
                  {metric.change}
                </span>
                <span className="text-sm text-gray-500 ml-1">
                  {metric.changeType === 'positive' || metric.changeType === 'negative' 
                    ? 'vs período anterior' 
                    : 'últimos 30 dias'}
                </span>
              </div>
            </div>
            <div className={`p-3 rounded-lg ${metric.color} bg-opacity-10`}>
              <div className={`${metric.color.replace('bg-', 'text-')}`}>
                {metric.icon}
              </div>
            </div>
          </div>
        </Card.Body>
      </Card>
    </motion.div>
  );

  if (loading) {
    return (
      <Layout title="Dashboard">
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl p-6 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              </div>
            ))}
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Dashboard">
      <div className="space-y-6">
        {/* Header Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-medium text-gray-900">
              Visão Geral do Sistema
            </h2>
            <p className="text-sm text-gray-500">
              Acompanhe o desempenho financeiro em tempo real
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="7d">Últimos 7 dias</option>
              <option value="30d">Últimos 30 dias</option>
              <option value="90d">Últimos 90 dias</option>
              <option value="1y">Último ano</option>
            </select>
            <Button
              variant="secondary"
              icon={<Filter className="w-4 h-4" />}
            >
              Filtros
            </Button>
          </div>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {metrics.map((metric, index) => (
            <MetricCard key={metric.title} metric={metric} index={index} />
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Transactions Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.4 }}
          >
            <Card>
              <Card.Header>
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">
                    Transações Recentes
                  </h3>
                  <Button variant="ghost" size="sm" href="/transactions">
                    Ver todas
                  </Button>
                </div>
              </Card.Header>
              <Card.Body>
                {transactionData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={transactionData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip
                        formatter={(value: number) => [
                          `R$ ${value.toLocaleString('pt-BR')}`,
                          'Valor',
                        ]}
                      />
                      <Line
                        type="monotone"
                        dataKey="amount"
                        stroke="#10B981"
                        strokeWidth={3}
                        dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-64 text-gray-500">
                    <div className="text-center">
                      <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p>Nenhuma transação encontrada</p>
                      <p className="text-sm">Adicione transações para ver os dados aqui</p>
                    </div>
                  </div>
                )}
              </Card.Body>
            </Card>
          </motion.div>

          {/* Accounts Distribution */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.5 }}
          >
            <Card>
              <Card.Header>
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">
                    Distribuição por Conta
                  </h3>
                  <Button variant="ghost" size="sm" href="/accounts">
                    Ver todas
                  </Button>
                </div>
              </Card.Header>
              <Card.Body>
                {accountData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={accountData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="balance"
                      >
                        {accountData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value: number) => [
                          `R$ ${value.toLocaleString('pt-BR')}`,
                          'Saldo',
                        ]}
                      />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-64 text-gray-500">
                    <div className="text-center">
                      <Wallet className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p>Nenhuma conta encontrada</p>
                      <p className="text-sm">Adicione contas para ver os dados aqui</p>
                    </div>
                  </div>
                )}
              </Card.Body>
            </Card>
          </motion.div>
        </div>

        {/* Recent Transactions List */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.6 }}
        >
          <Card>
            <Card.Header>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  Transações Recentes
                </h3>
                <Button variant="ghost" size="sm" href="/transactions">
                  Ver todas
                </Button>
              </div>
            </Card.Header>
            <Card.Body className="p-0">
              {recentTransactionsList.length > 0 ? (
                <div className="divide-y divide-gray-200">
                  {recentTransactionsList.map((transaction) => (
                    <div key={transaction.id} className="p-6 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div
                            className={`w-10 h-10 rounded-full flex items-center justify-center ${
                              transaction.type === 'credit'
                                ? 'bg-green-100'
                                : 'bg-red-100'
                            }`}
                          >
                            {transaction.type === 'credit' ? (
                              <TrendingUp className="w-5 h-5 text-green-600" />
                            ) : (
                              <TrendingDown className="w-5 h-5 text-red-600" />
                            )}
                          </div>
                          <div className="ml-4">
                            <p className="text-sm font-medium text-gray-900">
                              {transaction.description}
                            </p>
                            <p className="text-sm text-gray-500">
                              {new Date(transaction.date).toLocaleDateString('pt-BR')}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p
                            className={`text-sm font-medium ${
                              transaction.type === 'credit'
                                ? 'text-green-600'
                                : 'text-red-600'
                            }`}
                          >
                            {transaction.type === 'credit' ? '+' : '-'}
                            R$ {Math.abs(transaction.amount).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          </p>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Concluído
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center h-64 text-gray-500">
                  <div className="text-center">
                    <CreditCard className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>Nenhuma transação encontrada</p>
                    <p className="text-sm">Adicione transações para ver os dados aqui</p>
                  </div>
                </div>
              )}
            </Card.Body>
          </Card>
        </motion.div>
      </div>
    </Layout>
  );
}

