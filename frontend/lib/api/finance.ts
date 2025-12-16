import type { 
  AnnualSummaryResponse, 
  WalletResponse, 
  TransactionsResponse,
  MonthlyDailySummaryResponse,
  MonthlyTransactionsResponse
} from '../../types/dashboard';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://finaflow-backend-staging-642830139828.us-central1.run.app';

// Importação dinâmica do api para evitar SSR
const getApi = async () => {
  if (typeof window === 'undefined') {
    throw new Error('API só pode ser usada no cliente');
  }
  // Importar dinamicamente - o api é exportado como default
  const apiModule = await import('../../services/api');
  return apiModule.default;
};

// Função auxiliar para fazer requisições autenticadas
const fetchWithAuth = async (endpoint: string) => {
  try {
    const api = await getApi();
    const response = await api.get(endpoint);
    return response.data;
  } catch (error) {
    console.error(`Erro ao buscar dados de ${endpoint}:`, error);
    throw error;
  }
};

// Buscar resumo anual
export const fetchAnnualSummary = async (year: number): Promise<AnnualSummaryResponse> => {
  try {
    const data = await fetchWithAuth(`/api/v1/financial/annual-summary?year=${year}`);
    return data;
  } catch (error) {
    // Fallback: usar endpoint existente e transformar dados
    const cashFlowData = await fetchWithAuth('/api/v1/financial/cash-flow');
    
    // Transformar dados existentes para o formato anual
    const monthlyData: { [key: string]: any } = {};
    
    cashFlowData.forEach((item: any) => {
      const date = new Date(item.date);
      const monthKey = `${date.getFullYear()}-${date.getMonth() + 1}`;
      
      if (!monthlyData[monthKey]) {
            monthlyData[monthKey] = {
              month: date.getMonth() + 1,
              revenue: 0,
              expense: 0,
              cost: 0
            };
      }
      
      monthlyData[monthKey].revenue += item.total_revenue || 0;
      monthlyData[monthKey].expense += item.total_expenses || 0;
      monthlyData[monthKey].cost += item.total_costs || 0;
      monthlyData[monthKey].balance += item.net_flow || 0;
    });
    
    // Criar array com 12 meses
    const monthly = [];
    for (let month = 1; month <= 12; month++) {
      const monthKey = `${year}-${month}`;
      const monthData = monthlyData[monthKey] || {
        month,
        revenue: 0,
        expense: 0,
        cost: 0
      };
      
      monthly.push(monthData);
    }
    
    const totals = monthly.reduce((acc, month) => ({
      revenue: acc.revenue + month.revenue,
      expense: acc.expense + month.expense,
      cost: acc.cost + month.cost
    }), { revenue: 0, expense: 0, cost: 0 });
    
    return {
      year,
      totals,
      monthly
    };
  }
};

// Buscar dados da carteira/saldo disponível
export const fetchWallet = async (year: number): Promise<WalletResponse> => {
  try {
    const data = await fetchWithAuth(`/api/v1/financial/wallet?year=${year}`);
    return data;
  } catch (error) {
    // Fallback: usar endpoint existente
    const data = await fetchWithAuth('/api/v1/saldo-disponivel');
    const saldo = data.saldo_disponivel || data;
    
    return {
      year,
      bankAccounts: saldo.contas_bancarias?.detalhes?.map((conta: any) => ({
        label: conta.banco,
        amount: conta.saldo || 0
      })) || [],
      cash: saldo.caixas?.detalhes?.map((caixa: any) => ({
        label: caixa.nome,
        amount: caixa.saldo || 0
      })) || [],
      investments: saldo.investimentos?.detalhes?.map((inv: any) => ({
        label: inv.tipo,
        amount: inv.valor || 0
      })) || [],
      totalAvailable: saldo.total_geral || 0
    };
  }
};

// Buscar transações recentes
export const fetchTransactions = async (
  year: number, 
  limit: number = 10, 
  cursor?: string
): Promise<TransactionsResponse> => {
  try {
    const data = await fetchWithAuth(
      `/api/v1/financial/transactions?year=${year}&limit=${limit}&cursor=${cursor || ''}`
    );
    return data;
  } catch (error) {
    // Fallback: usar endpoint existente
    const data = await fetchWithAuth('/api/v1/lancamentos-diarios');
    
    // Filtrar por ano e transformar dados
    const yearTransactions = data.filter((item: any) => {
      const itemYear = new Date(item.data_movimentacao).getFullYear();
      return itemYear === year;
    }).slice(0, limit).map((item: any) => ({
      id: item.id,
      date: item.data_movimentacao,
      description: item.observacoes || 'Lançamento',
      type: item.transaction_type?.toLowerCase() as "revenue" | "expense" | "cost",
      amount: item.valor,
      account: item.conta?.name || 'Conta'
    }));
    
    return {
      year,
      items: yearTransactions,
      nextCursor: undefined
    };
  }
};

// Buscar resumo diário de um mês
export const fetchMonthlyDailySummary = async (
  year: number,
  month: number
): Promise<MonthlyDailySummaryResponse> => {
  try {
    const data = await fetchWithAuth(`/api/v1/financial/monthly-daily-summary?year=${year}&month=${month}`);
    return data;
  } catch (error) {
    console.error('Erro ao buscar resumo diário:', error);
    throw error;
  }
};

// Buscar lançamentos detalhados de um mês
export const fetchMonthlyTransactions = async (params: {
  year: number;
  month: number;
  type?: "RECEITA" | "DESPESA" | "CUSTO";
  group_id?: string;
  subgroup_id?: string;
  account_id?: string;
  page?: number;
  page_size?: number;
}): Promise<MonthlyTransactionsResponse> => {
  try {
    const queryParams = new URLSearchParams({
      year: params.year.toString(),
      month: params.month.toString(),
    });
    
    if (params.type) {
      queryParams.append('type', params.type);
    }
    if (params.group_id) {
      queryParams.append('group_id', params.group_id);
    }
    if (params.subgroup_id) {
      queryParams.append('subgroup_id', params.subgroup_id);
    }
    if (params.account_id) {
      queryParams.append('account_id', params.account_id);
    }
    if (params.page) {
      queryParams.append('page', params.page.toString());
    }
    if (params.page_size) {
      queryParams.append('page_size', params.page_size.toString());
    }
    
    const data = await fetchWithAuth(`/api/v1/financial/monthly-transactions?${queryParams.toString()}`);
    return data;
  } catch (error) {
    console.error('Erro ao buscar lançamentos mensais:', error);
    throw error;
  }
};

// ============================================================================
// DASHBOARD OPERACIONAL - ENDPOINTS
// ============================================================================

// Tipos para o dashboard operacional
export interface OperationalAvailability {
  banks: number;
  cash: number;
  investments: number;
  total: number;
}

export interface OperationalAlerts {
  overdue_payables: {
    count: number;
    value: number;
  };
  overdue_receivables: {
    count: number;
    value: number;
  };
  negative_cash_forecast: {
    has_alert: boolean;
    projected_balance: number;
    current_balance: number;
  };
}

export interface ForecastVsRealizedMonth {
  year: number;
  month: number;
  label: string;
  realized: number;
  forecast: number;
}

export interface ForecastVsRealized {
  months: ForecastVsRealizedMonth[];
  totals: {
    realized: number;
    forecast: number;
    difference: number;
  };
}

export interface PayablesSummary {
  overdue: number;
  due_today: number;
  next_7_days: number;
  next_30_days: number;
}

export interface ReceivablesSummary {
  overdue: number;
  due_today: number;
  next_7_days: number;
  next_30_days: number;
}

// Buscar disponibilidades de caixa
export const fetchOperationalAvailability = async (): Promise<OperationalAvailability> => {
  try {
    const data = await fetchWithAuth('/api/v1/dashboard/operational/availability');
    return data;
  } catch (error) {
    console.error('Erro ao buscar disponibilidades:', error);
    throw error;
  }
};

// Buscar alertas financeiros
export const fetchOperationalAlerts = async (): Promise<OperationalAlerts> => {
  try {
    const data = await fetchWithAuth('/api/v1/dashboard/operational/alerts');
    return data;
  } catch (error) {
    console.error('Erro ao buscar alertas:', error);
    throw error;
  }
};

// Buscar comparação previsto vs realizado
export const fetchForecastVsRealized = async (months: number = 6): Promise<ForecastVsRealized> => {
  try {
    const data = await fetchWithAuth(`/api/v1/operational/forecast-vs-realized?months=${months}`);
    return data;
  } catch (error) {
    console.error('Erro ao buscar previsto vs realizado:', error);
    throw error;
  }
};

// Buscar resumo de contas a pagar
export const fetchPayablesSummary = async (): Promise<PayablesSummary> => {
  try {
    const data = await fetchWithAuth('/api/v1/dashboard/operational/payables-summary');
    return data;
  } catch (error) {
    console.error('Erro ao buscar contas a pagar:', error);
    throw error;
  }
};

// Buscar resumo de contas a receber
export const fetchReceivablesSummary = async (): Promise<ReceivablesSummary> => {
  try {
    const data = await fetchWithAuth('/api/v1/dashboard/operational/receivables-summary');
    return data;
  } catch (error) {
    console.error('Erro ao buscar contas a receber:', error);
    throw error;
  }
};
