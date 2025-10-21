import api from '../../services/api';
import type { 
  AnnualSummaryResponse, 
  WalletResponse, 
  TransactionsResponse 
} from '../../types/dashboard';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://finaflow-backend-642830139828.us-central1.run.app';

// Função auxiliar para fazer requisições autenticadas
const fetchWithAuth = async (endpoint: string) => {
  try {
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
              cost: 0,
              balance: 0,
              caixa_final: 0
            };
      }
      
      monthlyData[monthKey].revenue += item.total_revenue || 0;
      monthlyData[monthKey].expense += item.total_expenses || 0;
      monthlyData[monthKey].cost += item.total_costs || 0;
      monthlyData[monthKey].balance += item.net_flow || 0;
    });
    
    // Criar array com 12 meses
    const monthly = [];
    let saldoAcumulado = 0;
    for (let month = 1; month <= 12; month++) {
      const monthKey = `${year}-${month}`;
      const monthData = monthlyData[monthKey] || {
        month,
        revenue: 0,
        expense: 0,
        cost: 0,
        balance: 0
      };
      
      // Calcular saldo acumulado
      saldoAcumulado += monthData.balance;
      monthData.caixa_final = saldoAcumulado;
      
      monthly.push(monthData);
    }
    
    const totals = monthly.reduce((acc, month) => ({
      revenue: acc.revenue + month.revenue,
      expense: acc.expense + month.expense,
      cost: acc.cost + month.cost,
      balance: acc.balance + month.balance
    }), { revenue: 0, expense: 0, cost: 0, balance: 0 });
    
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
