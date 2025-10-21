export type MonthlyBreakdown = {
  month: number;        // 1..12
  revenue: number;      // receitas
  expense: number;      // despesas
  cost: number;         // custos
};

export type AnnualSummaryResponse = {
  year: number;
  totals: {
    revenue: number;
    expense: number;
    cost: number;
  };
  monthly: MonthlyBreakdown[]; // 12 entradas, meses ausentes devem vir como 0
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
