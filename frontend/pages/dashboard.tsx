import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Calendar } from 'lucide-react';
import Layout from '../components/layout/Layout';
import { useAuth } from '../context/AuthContext';
import { useYearFilter } from '../lib/hooks/useYearFilter';
import { fetchAnnualSummary, fetchWallet, fetchTransactions } from '../lib/api/finance';
import YearSelect from '../components/YearSelect';
import AnnualCards from '../components/cards/AnnualCards';
import AnnualLineChart from '../components/charts/AnnualLineChart';
import AnnualMonthlyTable from '../components/tables/AnnualMonthlyTable';
import WalletCard from '../components/cards/WalletCard';
import RecentTransactionsCard from '../components/cards/RecentTransactionsCard';
import type { AnnualSummaryResponse, WalletResponse, TransactionsResponse } from '../types/dashboard';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { year, setYear, isLoading: yearLoading } = useYearFilter();
  
  // Estados dos dados
  const [annualData, setAnnualData] = useState<AnnualSummaryResponse | null>(null);
  const [walletData, setWalletData] = useState<WalletResponse | null>(null);
  const [transactionsData, setTransactionsData] = useState<TransactionsResponse | null>(null);
  
  // Estados de loading e erro
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Carregar dados quando o ano muda
  useEffect(() => {
    if (year) {
      loadDashboardData();
    }
  }, [year]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Carregar todos os dados em paralelo
      const [summaryData, walletDataResult, transactionsDataResult] = await Promise.all([
        fetchAnnualSummary(year),
        fetchWallet(year),
        fetchTransactions(year, 10)
      ]);

      setAnnualData(summaryData);
      setWalletData(walletDataResult);
      setTransactionsData(transactionsDataResult);

    } catch (err) {
      console.error('Erro ao carregar dados do dashboard:', err);
      setError(`Falha ao carregar dados do ano ${year}. Tente novamente.`);
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (loading && !annualData) {
    return (
      <Layout title="Dashboard">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  // Error state
  if (error) {
    return (
      <Layout title="Dashboard">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={loadDashboardData}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Tentar Novamente
            </button>
          </div>
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
              Bem-vindo ao seu dashboard financeiro anual
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <YearSelect 
              year={year} 
              onYearChange={setYear}
              disabled={yearLoading || loading}
            />
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Calendar className="w-4 h-4" />
              <span>{new Date().toLocaleDateString('pt-BR')}</span>
            </div>
          </div>
        </div>

        {/* Cards Principais */}
        {annualData && (
          <AnnualCards 
            data={annualData} 
            isLoading={loading}
          />
        )}

        {/* Gráfico de Evolução Mensal */}
        {annualData && (
          <AnnualLineChart 
            data={annualData} 
            isLoading={loading}
          />
        )}

        {/* Tabela Resumo Mensal */}
        {annualData && (
          <AnnualMonthlyTable 
            data={annualData} 
            isLoading={loading}
          />
        )}

        {/* Saldo Disponível */}
        {walletData && (
          <WalletCard 
            data={walletData} 
            isLoading={loading}
          />
        )}

        {/* Transações Recentes */}
        {transactionsData && (
          <RecentTransactionsCard 
            data={transactionsData}
            year={year}
            isLoading={loading}
          />
        )}

        {/* Empty State */}
        {!annualData && !loading && !error && (
          <div className="text-center py-12">
            <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Sem dados para este ano
            </h3>
            <p className="text-gray-500">
              Não há dados financeiros disponíveis para {year}.
            </p>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Dashboard;