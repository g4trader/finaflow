export type MonthlyBreakdown = {
  month: number;        // 1..12
  revenue: number;      // receitas
  expense: number;      // despesas
  cost: number;         // custos
  balance: number;      // saldo_mensal = receita - despesa - custo
  accumulated_balance: number; // saldo_acumulado = soma progressiva dos saldos mensais
};

export type AnnualSummaryResponse = {
  year: number;
  totals: {
    revenue: number;
    expense: number;
    cost: number;
    balance: number;    // saldo total anual
  };
  monthly: MonthlyBreakdown[]; // 12 entradas, meses ausentes devem vir como 0
  metadata?: {
    saldo_formula: string;
    saldo_acumulado_formula: string;
    saldo_acumulado_explanation: string;
    calculation_precision: string;
    empty_months_behavior: string;
  };
  ytdComparison?: { 
    currentYTD: number; 
    lastYearYTD: number 
  }; // opcional para tendência
};

export type WalletResponse = {
  year: number;
  bankAccounts: { label: string; amount: number }[];
  cash: { label: string; amount: number }[];
  investments: { label: string; amount: number }[];
  totalAvailable: number; // soma de todos
};

export type TransactionsResponse = {
  year: number;
  items: Array<{
    id: string;
    date: string;       // ISO
    description: string;
    type: "revenue" | "expense" | "cost";
    amount: number;
    account: string;
  }>;
  nextCursor?: string;
};

export type YearFilterState = {
  year: number;
  setYear: (year: number) => void;
  isLoading: boolean;
};

export interface MonthlyDailySummaryResponse {
  year: number;
  month: number;
  currency: string;
  days: {
    date: string;  // ISO format
    day: number;
    revenue: string;
    expense: string;
    cost: string;
    balance: string;
  }[];
  metadata: {
    saldo_formula: string;
    saldo_acumulado_formula?: string;
    month_total_revenue: string;
    month_total_expense: string;
    month_total_cost: string;
    month_total_balance: string;
  };
}

export interface MonthlyTransactionsResponse {
  year: number;
  month: number;
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  summary: {
    revenue: string;
    expense: string;
    cost: string;
    balance: string;
  };
  items: {
    id: string;
    date: string;
    description: string;
    type: "RECEITA" | "DESPESA" | "CUSTO";
    group?: string | null;
    subgroup?: string | null;
    account?: string | null;
    amount: string;
  }[];
}
