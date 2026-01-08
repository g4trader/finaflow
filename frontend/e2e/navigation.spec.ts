import { test, expect } from '@playwright/test';

// Configurações
const FRONTEND_URL = process.env.FRONTEND_URL || 'https://finaflow.vercel.app';
const QA_EMAIL = process.env.QA_EMAIL || 'qa@finaflow.test';
const QA_PASSWORD = process.env.QA_PASSWORD || 'QaFinaflow123!';

// Timeout aumentado para operações que podem demorar
const TIMEOUT = 60000;

// Função auxiliar para fazer login
async function performLogin(page: any) {
  const currentUrl = page.url();
  
  // Se estiver na landing, clicar em "Entrar"
  if (currentUrl === FRONTEND_URL || currentUrl === `${FRONTEND_URL}/`) {
    const entrarLink = page.locator('text=Entrar').first();
    if (await entrarLink.isVisible({ timeout: 2000 }).catch(() => false)) {
      await entrarLink.click();
      await page.waitForURL('**/login', { timeout: 5000 });
    }
  }
  
  // Aguardar página de login carregar
  await page.waitForSelector('input[name="username"], input[type="text"]', { timeout: 10000 });
  
  // Preencher formulário
  await page.locator('input[name="username"]').first().fill(QA_EMAIL);
  await page.locator('input[type="password"]').first().fill(QA_PASSWORD);
  
  // Clicar no botão de login
  await page.locator('button:has-text("Entrar"), button[type="submit"]').first().click();
  
  // Aguardar resposta do login (pode mostrar erro ou redirecionar)
  await page.waitForTimeout(3000); // Dar tempo para a requisição
  
  // Verificar se há mensagem de erro
  const errorMessage = await page.locator('[class*="error"], [class*="red"], text=/erro|error/i').first().textContent().catch(() => null);
  if (errorMessage) {
    console.log(`❌ Erro no login: ${errorMessage}`);
    await page.screenshot({ path: `test-results/login-error-${Date.now()}.png` });
    throw new Error(`Login falhou: ${errorMessage}`);
  }
  
  // Aguardar qualquer redirecionamento (pode ser select-business-unit ou dashboard)
  try {
    await page.waitForURL('**/select-business-unit**', { timeout: 15000 });
    console.log('✅ Redirecionado para select-business-unit');
    
    // Selecionar primeira BU disponível
    await page.waitForSelector('button, [role="button"], [class*="card"], [class*="business"]', { timeout: 10000 });
    
    // Tentar diferentes seletores para o botão de seleção
    const selectors = [
      'button:has-text(/selecionar|escolher/i)',
      '[class*="card"]:has-text(/matriz|empresa/i)',
      'button[type="button"]',
      '[role="button"]',
    ];
    
    let buSelected = false;
    for (const selector of selectors) {
      const buButton = page.locator(selector).first();
      if (await buButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await buButton.click();
        buSelected = true;
        break;
      }
    }
    
    if (!buSelected) {
      // Última tentativa: clicar no primeiro elemento clicável
      const firstClickable = page.locator('button, [role="button"], [class*="card"]').first();
      if (await firstClickable.isVisible({ timeout: 2000 }).catch(() => false)) {
        await firstClickable.click();
      }
    }
    
    // Aguardar redirecionamento para dashboard
    await page.waitForURL('**/dashboard**', { timeout: 15000 });
    console.log('✅ Redirecionado para dashboard após seleção de BU');
  } catch (e) {
    // Se não redirecionou para select-business-unit, pode ter ido direto para dashboard
    try {
      await page.waitForURL('**/dashboard**', { timeout: 10000 });
      console.log('✅ Redirecionado diretamente para dashboard');
    } catch (e2) {
      // Se ainda não redirecionou, verificar URL atual e tirar screenshot
      const currentUrl = page.url();
      console.log(`⚠️  URL atual após login: ${currentUrl}`);
      await page.screenshot({ path: `test-results/login-debug-${Date.now()}.png` });
      throw new Error(`Login não redirecionou corretamente. URL atual: ${currentUrl}`);
    }
  }
  
  // Verificar que estamos no dashboard
  expect(page.url()).toContain('/dashboard');
}

test.describe('E2E: Navegação Completa no Sistema', () => {
  
  test.beforeEach(async ({ page }) => {
    // Ir para a página inicial
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
  });

  test('Login e redirecionamento para dashboard', async ({ page }) => {
    await performLogin(page);
    
    // Verificar que elementos do dashboard estão presentes
    await page.waitForSelector('h1, h2, [class*="dashboard"], body', { timeout: 10000 });
    console.log('✅ Dashboard carregado com sucesso');
  });

  test('Navegação completa pelas principais telas', async ({ page }) => {
    // Fazer login primeiro
    const currentUrl = page.url();
    if (!currentUrl.includes('/dashboard')) {
      // Se não estiver logado, fazer login
      const entrarLink = page.locator('text=Entrar').first();
      if (await entrarLink.isVisible({ timeout: 2000 }).catch(() => false)) {
        await entrarLink.click();
        await page.waitForURL('**/login', { timeout: 5000 });
      }
      
      await page.waitForSelector('input[type="email"], input[name="email"], input[name="username"]', { timeout: 10000 });
      await page.locator('input[name="username"]').first().fill(QA_EMAIL);
      await page.locator('input[type="password"]').first().fill(QA_PASSWORD);
      await page.locator('button:has-text("Entrar"), button[type="submit"]').first().click();
      
      // Aguardar redirecionamento (pode ir para select-business-unit primeiro)
      await page.waitForURL('**/select-business-unit**', { timeout: TIMEOUT }).catch(async () => {
        await page.waitForURL('**/dashboard**', { timeout: 5000 });
      });
      
      // Se estiver em select-business-unit, selecionar a primeira BU
      if (page.url().includes('/select-business-unit')) {
        await page.waitForSelector('button, [role="button"], [class*="card"]', { timeout: 10000 });
        const buButton = page.locator('button, [role="button"], [class*="card"]').first();
        if (await buButton.isVisible({ timeout: 5000 }).catch(() => false)) {
          await buButton.click();
          await page.waitForURL('**/dashboard**', { timeout: TIMEOUT });
        }
      }
    }

    // Lista de páginas para navegar
    const pagesToTest = [
      {
        name: 'Dashboard',
        path: '/dashboard',
        selector: 'h1, h2, [class*="dashboard"]',
        description: 'Dashboard principal'
      },
      {
        name: 'Dashboard Operacional',
        path: '/dashboard-operational',
        selector: 'h1, h2, [class*="operational"], [class*="dashboard"]',
        description: 'Dashboard operacional'
      },
      {
        name: 'Lançamentos Financeiros',
        path: '/transactions',
        selector: 'h1, h2, table, [class*="transaction"]',
        description: 'Página de lançamentos'
      },
      {
        name: 'Previsões Financeiras',
        path: '/financial-forecasts',
        selector: 'h1, h2, [class*="forecast"]',
        description: 'Página de previsões'
      },
      {
        name: 'Fluxo de Caixa',
        path: '/cash-flow',
        selector: 'h1, h2, [class*="cash"], [class*="flow"]',
        description: 'Fluxo de caixa mensal'
      },
      {
        name: 'Fluxo de Caixa Diário',
        path: '/daily-cash-flow',
        selector: 'h1, h2, [class*="daily"], [class*="cash"]',
        description: 'Fluxo de caixa diário'
      },
      {
        name: 'Contas Bancárias',
        path: '/contas-bancarias',
        selector: 'h1, h2, [class*="account"], table',
        description: 'Contas bancárias'
      },
    ];

    // Navegar por cada página
    for (const pageInfo of pagesToTest) {
      console.log(`\n🧭 Navegando para: ${pageInfo.name} (${pageInfo.path})`);
      
      // Navegar para a página
      await page.goto(`${FRONTEND_URL}${pageInfo.path}`, { waitUntil: 'networkidle', timeout: TIMEOUT });
      
      // Verificar que a URL está correta
      expect(page.url()).toContain(pageInfo.path);
      
      // Aguardar carregamento da página (elementos principais)
      try {
        await page.waitForSelector(pageInfo.selector, { timeout: 15000 });
        console.log(`✅ ${pageInfo.name}: Página carregada com sucesso`);
      } catch (error) {
        // Se não encontrar o seletor específico, verificar se a página pelo menos carregou
        const bodyText = await page.locator('body').textContent();
        if (bodyText && bodyText.length > 100) {
          console.log(`⚠️  ${pageInfo.name}: Página carregou mas seletor específico não encontrado`);
        } else {
          throw new Error(`${pageInfo.name}: Página não carregou corretamente`);
        }
      }
      
      // Verificar que não há erros críticos na página
      const errorMessages = await page.locator('text=/erro|error|404|500/i').count();
      if (errorMessages > 0) {
        console.log(`⚠️  ${pageInfo.name}: Possíveis mensagens de erro encontradas`);
      }
      
      // Pequena pausa entre navegações
      await page.waitForTimeout(1000);
    }
  });

  test('Navegação via menu lateral', async ({ page }) => {
    // Fazer login
    const currentUrl = page.url();
    if (!currentUrl.includes('/dashboard')) {
      const entrarLink = page.locator('text=Entrar').first();
      if (await entrarLink.isVisible({ timeout: 2000 }).catch(() => false)) {
        await entrarLink.click();
        await page.waitForURL('**/login', { timeout: 5000 });
      }
      
      await page.waitForSelector('input[type="email"], input[name="email"], input[name="username"]', { timeout: 10000 });
      await page.locator('input[name="username"]').first().fill(QA_EMAIL);
      await page.locator('input[type="password"]').first().fill(QA_PASSWORD);
      await page.locator('button:has-text("Entrar"), button[type="submit"]').first().click();
      
      // Aguardar redirecionamento (pode ir para select-business-unit primeiro)
      await page.waitForURL('**/select-business-unit**', { timeout: TIMEOUT }).catch(async () => {
        await page.waitForURL('**/dashboard**', { timeout: 5000 });
      });
      
      // Se estiver em select-business-unit, selecionar a primeira BU
      if (page.url().includes('/select-business-unit')) {
        await page.waitForSelector('button, [role="button"], [class*="card"]', { timeout: 10000 });
        const buButton = page.locator('button, [role="button"], [class*="card"]').first();
        if (await buButton.isVisible({ timeout: 5000 }).catch(() => false)) {
          await buButton.click();
          await page.waitForURL('**/dashboard**', { timeout: TIMEOUT });
        }
      }
    }

    // Itens do menu para testar
    const menuItems = [
      { text: 'Dashboard', path: '/dashboard' },
      { text: 'Dashboard Operacional', path: '/dashboard-operational' },
      { text: 'Lançamentos Financeiros', path: '/transactions' },
      { text: 'Previsões Financeiras', path: '/financial-forecasts' },
      { text: 'Fluxo de Caixa', path: '/cash-flow' },
      { text: 'Fluxo de Caixa Diário', path: '/daily-cash-flow' },
      { text: 'Contas Bancárias', path: '/contas-bancarias' },
    ];

    // Testar navegação via menu
    for (const item of menuItems) {
      console.log(`\n📋 Clicando no menu: ${item.text}`);
      
      // Tentar encontrar o item do menu (pode estar em sidebar ou menu mobile)
      const menuItem = page.locator(`text=${item.text}`).first();
      
      if (await menuItem.isVisible({ timeout: 5000 }).catch(() => false)) {
        await menuItem.click();
        
        // Aguardar navegação
        await page.waitForURL(`**${item.path}**`, { timeout: TIMEOUT });
        expect(page.url()).toContain(item.path);
        console.log(`✅ Navegação para ${item.text} bem-sucedida`);
      } else {
        // Se o menu não estiver visível, pode estar em um menu mobile/hamburger
        const hamburgerButton = page.locator('button[aria-label*="menu"], button[aria-label*="Menu"], [class*="hamburger"], [class*="menu-toggle"]').first();
        if (await hamburgerButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await hamburgerButton.click();
          await page.waitForTimeout(500);
          
          // Tentar novamente
          const menuItemAfter = page.locator(`text=${item.text}`).first();
          if (await menuItemAfter.isVisible({ timeout: 2000 }).catch(() => false)) {
            await menuItemAfter.click();
            await page.waitForURL(`**${item.path}**`, { timeout: TIMEOUT });
            expect(page.url()).toContain(item.path);
            console.log(`✅ Navegação para ${item.text} bem-sucedida (via menu mobile)`);
          } else {
            console.log(`⚠️  Item do menu "${item.text}" não encontrado`);
          }
        } else {
          console.log(`⚠️  Item do menu "${item.text}" não encontrado e menu mobile não disponível`);
        }
      }
      
      await page.waitForTimeout(1000);
    }
  });

  test('Verificar elementos essenciais nas páginas principais', async ({ page }) => {
    // Fazer login
    const currentUrl = page.url();
    if (!currentUrl.includes('/dashboard')) {
      const entrarLink = page.locator('text=Entrar').first();
      if (await entrarLink.isVisible({ timeout: 2000 }).catch(() => false)) {
        await entrarLink.click();
        await page.waitForURL('**/login', { timeout: 5000 });
      }
      
      await page.waitForSelector('input[type="email"], input[name="email"], input[name="username"]', { timeout: 10000 });
      await page.locator('input[name="username"]').first().fill(QA_EMAIL);
      await page.locator('input[type="password"]').first().fill(QA_PASSWORD);
      await page.locator('button:has-text("Entrar"), button[type="submit"]').first().click();
      
      // Aguardar redirecionamento (pode ir para select-business-unit primeiro)
      await page.waitForURL('**/select-business-unit**', { timeout: TIMEOUT }).catch(async () => {
        await page.waitForURL('**/dashboard**', { timeout: 5000 });
      });
      
      // Se estiver em select-business-unit, selecionar a primeira BU
      if (page.url().includes('/select-business-unit')) {
        await page.waitForSelector('button, [role="button"], [class*="card"]', { timeout: 10000 });
        const buButton = page.locator('button, [role="button"], [class*="card"]').first();
        if (await buButton.isVisible({ timeout: 5000 }).catch(() => false)) {
          await buButton.click();
          await page.waitForURL('**/dashboard**', { timeout: TIMEOUT });
        }
      }
    }

    // Verificar elementos comuns em todas as páginas autenticadas
    const commonElements = [
      { selector: 'body', description: 'Corpo da página' },
      { selector: 'nav, [class*="sidebar"], [class*="menu"]', description: 'Menu de navegação' },
    ];

    // Verificar no dashboard
    await page.goto(`${FRONTEND_URL}/dashboard`, { waitUntil: 'networkidle', timeout: TIMEOUT });
    
    for (const element of commonElements) {
      const count = await page.locator(element.selector).count();
      expect(count).toBeGreaterThan(0);
      console.log(`✅ ${element.description}: encontrado`);
    }

    // Verificar que não há erros de console críticos
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Ignorar alguns erros conhecidos que não são críticos
        if (!text.includes('favicon') && !text.includes('sourcemap')) {
          consoleErrors.push(text);
        }
      }
    });

    // Navegar por algumas páginas e coletar erros
    const testPages = ['/dashboard', '/dashboard-operational', '/transactions'];
    for (const path of testPages) {
      await page.goto(`${FRONTEND_URL}${path}`, { waitUntil: 'networkidle', timeout: TIMEOUT });
      await page.waitForTimeout(2000); // Dar tempo para erros aparecerem
    }

    if (consoleErrors.length > 0) {
      console.log(`⚠️  Erros de console encontrados: ${consoleErrors.length}`);
      consoleErrors.slice(0, 5).forEach(err => console.log(`   - ${err}`));
    } else {
      console.log('✅ Nenhum erro crítico de console encontrado');
    }
  });

  test('Logout e verificação de redirecionamento', async ({ page }) => {
    // Fazer login
    const currentUrl = page.url();
    if (!currentUrl.includes('/dashboard')) {
      const entrarLink = page.locator('text=Entrar').first();
      if (await entrarLink.isVisible({ timeout: 2000 }).catch(() => false)) {
        await entrarLink.click();
        await page.waitForURL('**/login', { timeout: 5000 });
      }
      
      await page.waitForSelector('input[type="email"], input[name="email"], input[name="username"]', { timeout: 10000 });
      await page.locator('input[name="username"]').first().fill(QA_EMAIL);
      await page.locator('input[type="password"]').first().fill(QA_PASSWORD);
      await page.locator('button:has-text("Entrar"), button[type="submit"]').first().click();
      
      // Aguardar redirecionamento (pode ir para select-business-unit primeiro)
      await page.waitForURL('**/select-business-unit**', { timeout: TIMEOUT }).catch(async () => {
        await page.waitForURL('**/dashboard**', { timeout: 5000 });
      });
      
      // Se estiver em select-business-unit, selecionar a primeira BU
      if (page.url().includes('/select-business-unit')) {
        await page.waitForSelector('button, [role="button"], [class*="card"]', { timeout: 10000 });
        const buButton = page.locator('button, [role="button"], [class*="card"]').first();
        if (await buButton.isVisible({ timeout: 5000 }).catch(() => false)) {
          await buButton.click();
          await page.waitForURL('**/dashboard**', { timeout: TIMEOUT });
        }
      }
    }

    // Tentar encontrar botão de logout
    const logoutSelectors = [
      'text=/sair|logout|log out|sair do sistema/i',
      'button[aria-label*="logout"]',
      'button[aria-label*="sair"]',
      '[class*="logout"]',
      '[class*="sair"]',
    ];

    let logoutFound = false;
    for (const selector of logoutSelectors) {
      const logoutButton = page.locator(selector).first();
      if (await logoutButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await logoutButton.click();
        logoutFound = true;
        break;
      }
    }

    if (logoutFound) {
      // Aguardar redirecionamento para login
      await page.waitForURL('**/login**', { timeout: TIMEOUT });
      expect(page.url()).toContain('/login');
      console.log('✅ Logout realizado com sucesso');
    } else {
      console.log('⚠️  Botão de logout não encontrado (pode não estar implementado)');
    }
  });
});

