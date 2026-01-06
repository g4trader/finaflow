import { test, expect } from '@playwright/test';

// Configurações
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://finaflow-backend-staging-556803510516.us-central1.run.app';
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000';
const YEAR = 2025;

// Função auxiliar para fazer login e obter token
async function loginAPI(): Promise<string | null> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'qa@finaflow.test',
        password: 'QaFinaflow123!',
      }),
    });

    if (!response.ok) {
      console.error('Erro ao fazer login:', response.statusText);
      return null;
    }

    const data = await response.json();
    return data.access_token || data.token || null;
  } catch (error) {
    console.error('Erro ao fazer login:', error);
    return null;
  }
}

// Função auxiliar para buscar dados da API
async function fetchAnnualSummary(token: string): Promise<any> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/financial/annual-summary?year=${YEAR}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`API retornou ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erro ao buscar annual-summary:', error);
    throw error;
  }
}

// Função auxiliar para converter texto BRL para número
function parseBRL(text: string): number {
  // Remove "R$", espaços, pontos (milhares) e substitui vírgula (decimal) por ponto
  const cleaned = text
    .replace(/R\$/g, '')
    .replace(/\s/g, '')
    .replace(/\./g, '')
    .replace(',', '.');
  
  return parseFloat(cleaned) || 0;
}

// Função auxiliar para comparar valores com tolerância (centavos)
function compareValues(expected: number, actual: number, tolerance: number = 0.01): boolean {
  return Math.abs(expected - actual) <= tolerance;
}

test.describe('E2E: Consistência Planilha → API → UI', () => {
  let apiData: any;
  let token: string | null;

  test.beforeAll(async () => {
    // Fazer login e buscar dados da API
    token = await loginAPI();
    if (!token) {
      throw new Error('Falha ao fazer login na API');
    }

    apiData = await fetchAnnualSummary(token);
  });

  test('Totais anuais batem entre API e UI', async ({ page }) => {
    // Navegar para o dashboard
    await page.goto(`${FRONTEND_URL}/dashboard?year=${YEAR}`);

    // Aguardar carregamento
    await page.waitForSelector('table', { timeout: 10000 });

    // Buscar totais na UI (assumindo que estão em elementos com classes específicas ou texto)
    // Ajustar seletores conforme a estrutura real do frontend
    const totalReceitaText = await page.locator('text=/Receita.*Total|Total.*Receita/i').first().textContent() || '0';
    const totalDespesaText = await page.locator('text=/Despesa.*Total|Total.*Despesa/i').first().textContent() || '0';
    const totalCustoText = await page.locator('text=/Custo.*Total|Total.*Custo/i').first().textContent() || '0';

    // Converter para números
    const totalReceitaUI = parseBRL(totalReceitaText);
    const totalDespesaUI = parseBRL(totalDespesaText);
    const totalCustoUI = parseBRL(totalCustoText);

    // Obter totais da API
    const totals = apiData.totals || {};
    const totalReceitaAPI = totals.revenue || 0;
    const totalDespesaAPI = totals.expense || 0;
    const totalCustoAPI = totals.cost || 0;

    // Comparar
    expect(compareValues(totalReceitaAPI, totalReceitaUI), 
      `Receita: API=${totalReceitaAPI}, UI=${totalReceitaUI}`).toBeTruthy();
    expect(compareValues(totalDespesaAPI, totalDespesaUI),
      `Despesa: API=${totalDespesaAPI}, UI=${totalDespesaUI}`).toBeTruthy();
    expect(compareValues(totalCustoAPI, totalCustoUI),
      `Custo: API=${totalCustoAPI}, UI=${totalCustoUI}`).toBeTruthy();
  });

  test('Tabela mensal tem 12 meses', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard?year=${YEAR}`);
    await page.waitForSelector('table', { timeout: 10000 });

    // Contar linhas da tabela mensal (assumindo que cada mês é uma linha)
    // Ajustar seletor conforme estrutura real
    const monthRows = await page.locator('table tbody tr').count();
    
    // Deve ter 12 meses + possivelmente linha de totais
    expect(monthRows).toBeGreaterThanOrEqual(12);
  });

  test('Meses Jan, Jun, Dez batem entre API e UI', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard?year=${YEAR}`);
    await page.waitForSelector('table', { timeout: 10000 });

    const mesesParaVerificar = [
      { nome: 'Janeiro', numero: 1 },
      { nome: 'Junho', numero: 6 },
      { nome: 'Dezembro', numero: 12 },
    ];

    for (const mes of mesesParaVerificar) {
      // Buscar dados da API para o mês
      const monthlyData = apiData.monthly || [];
      const monthAPI = monthlyData.find((m: any) => m.month === mes.numero);
      
      if (!monthAPI) {
        throw new Error(`Mês ${mes.numero} não encontrado na API`);
      }

      // Buscar linha na tabela (ajustar seletor conforme estrutura real)
      const monthRow = page.locator(`text=${mes.nome}`).locator('..').locator('..');
      
      // Extrair valores da UI (ajustar conforme estrutura real)
      // Assumindo que os valores estão em células específicas
      const revenueCell = monthRow.locator('td').nth(1); // Ajustar índice
      const expenseCell = monthRow.locator('td').nth(2);
      const costCell = monthRow.locator('td').nth(3);
      const balanceCell = monthRow.locator('td').nth(4);
      const accumulatedBalanceCell = monthRow.locator('td').nth(5);

      const revenueUIText = await revenueCell.textContent() || '0';
      const expenseUIText = await expenseCell.textContent() || '0';
      const costUIText = await costCell.textContent() || '0';
      const balanceUIText = await balanceCell.textContent() || '0';
      const accumulatedBalanceUIText = await accumulatedBalanceCell.textContent() || '0';

      const revenueUI = parseBRL(revenueUIText);
      const expenseUI = parseBRL(expenseUIText);
      const costUI = parseBRL(costUIText);
      const balanceUI = parseBRL(balanceUIText);
      const accumulatedBalanceUI = parseBRL(accumulatedBalanceUIText);

      // Comparar com API
      expect(compareValues(monthAPI.revenue, revenueUI),
        `Mês ${mes.numero} - Receita: API=${monthAPI.revenue}, UI=${revenueUI}`).toBeTruthy();
      expect(compareValues(monthAPI.expense, expenseUI),
        `Mês ${mes.numero} - Despesa: API=${monthAPI.expense}, UI=${expenseUI}`).toBeTruthy();
      expect(compareValues(monthAPI.cost, costUI),
        `Mês ${mes.numero} - Custo: API=${monthAPI.cost}, UI=${costUI}`).toBeTruthy();
      expect(compareValues(monthAPI.balance, balanceUI),
        `Mês ${mes.numero} - Saldo: API=${monthAPI.balance}, UI=${balanceUI}`).toBeTruthy();
      expect(compareValues(monthAPI.accumulated_balance, accumulatedBalanceUI),
        `Mês ${mes.numero} - Saldo Acumulado: API=${monthAPI.accumulated_balance}, UI=${accumulatedBalanceUI}`).toBeTruthy();
    }
  });
});

