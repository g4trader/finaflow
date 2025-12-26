import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import CashAvailabilityCards from '../components/cards/CashAvailabilityCards';
import CashCoverageIndicator from '../components/cards/CashCoverageIndicator';
import FinancialAlerts from '../components/cards/FinancialAlerts';
import ForecastVsRealizedChart from '../components/charts/ForecastVsRealizedChart';
import PayablesSummaryCard from '../components/cards/PayablesSummaryCard';
import ReceivablesSummaryCard from '../components/cards/ReceivablesSummaryCard';
import {
  fetchOperationalAvailability,
  fetchOperationalAlerts,
  fetchForecastVsRealized,
  fetchPayablesSummary,
  fetchReceivablesSummary,
  type OperationalAvailability,
  type OperationalAlerts,
  type ForecastVsRealized,
  type PayablesSummary,
  type ReceivablesSummary,
} from '../lib/api/finance';

const DashboardOperational: React.FC = () => {
  const [availability, setAvailability] = useState<OperationalAvailability | null>(null);
  const [alerts, setAlerts] = useState<OperationalAlerts | null>(null);
  const [forecastVsRealized, setForecastVsRealized] = useState<ForecastVsRealized | null>(null);
  const [payables, setPayables] = useState<PayablesSummary | null>(null);
  const [receivables, setReceivables] = useState<ReceivablesSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Carregar todos os dados em paralelo
      const [availabilityData, alertsData, forecastData, payablesData, receivablesData] = await Promise.all([
        fetchOperationalAvailability(),
        fetchOperationalAlerts(),
        fetchForecastVsRealized(6),
        fetchPayablesSummary(),
        fetchReceivablesSummary(),
      ]);

      setAvailability(availabilityData);
      setAlerts(alertsData);
      setForecastVsRealized(forecastData);
      setPayables(payablesData);
      setReceivables(receivablesData);
    } catch (err: any) {
      console.error('Erro ao carregar dados do dashboard operacional:', err);
      setError(err.message || 'Falha ao carregar dados do dashboard operacional.');
    } finally {
      setLoading(false);
    }
  };

  const handleAlertClick = (type: string) => {
    // Navegar para a tela filtrada correspondente
    // Por enquanto, apenas log
    console.log('Alert clicked:', type);
    // TODO: Implementar navegação para tela filtrada
  };

  const handlePayablesDetails = () => {
    // Navegar para lista de contas a pagar
    console.log('View payables details');
    // TODO: Implementar navegação
  };

  const handleReceivablesDetails = () => {
    // Navegar para lista de contas a receber
    console.log('View receivables details');
    // TODO: Implementar navegação
  };

  if (loading) {
    return (
      <Layout title="Dashboard Operacional">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout title="Dashboard Operacional">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
          <button
            onClick={loadDashboardData}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Tentar novamente
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Dashboard Operacional">
      <div className="container mx-auto px-4 py-6">
        <h1 className="text-3xl font-bold mb-6 text-gray-800">Dashboard Financeiro Operacional</h1>

        {/* Bloco 1: Composição das Disponibilidades (Total em destaque) */}
        {availability && <CashAvailabilityCards data={availability} />}

        {/* Bloco 2: Cobertura de Caixa (Novo indicador) */}
        {availability && payables && (
          <CashCoverageIndicator availability={availability} payables={payables} />
        )}

        {/* Bloco 3: Alertas Financeiros (Visual crítico) */}
        {alerts && (
          <FinancialAlerts data={alerts} onAlertClick={handleAlertClick} />
        )}

        {/* Bloco 4: Previsto × Realizado (Gráfico com zero como referência) */}
        {forecastVsRealized && (
          <ForecastVsRealizedChart data={forecastVsRealized} />
        )}

        {/* Bloco 5 e 6: Contas a Receber e a Pagar (Simplificados) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          {receivables && (
            <ReceivablesSummaryCard
              data={receivables}
              onViewDetails={handleReceivablesDetails}
            />
          )}
          {payables && (
            <PayablesSummaryCard
              data={payables}
              onViewDetails={handlePayablesDetails}
            />
          )}
        </div>
      </div>
    </Layout>
  );
};

export default DashboardOperational;






