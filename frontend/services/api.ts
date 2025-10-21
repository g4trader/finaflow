import axios from 'axios';

// Build timestamp: 2025-09-02 12:00:00 - Fixed backend URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://finaflow-backend-642830139828.us-central1.run.app';

// Log da URL da API (para debug)
if (typeof window !== 'undefined') {
  console.log('🔧 [API Config] API Base URL:', API_BASE_URL);
  console.log('🔧 [API Config] NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
}

// Configuração do axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,  // Temporariamente desabilitar credentials para CORS funcionar
});

// Interceptor para adicionar token de autenticação
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Interceptor para tratamento de erros
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expirado, tentar renovar
      try {
        const refreshToken = localStorage.getItem('refresh-token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const newToken = response.data.access_token;
          localStorage.setItem('token', newToken);
          
          // Reenviar requisição original com novo token
          error.config.headers.Authorization = `Bearer ${newToken}`;
          return axios(error.config);
        }
      } catch (refreshError) {
        // Falha ao renovar token, redirecionar para login
        localStorage.removeItem('token');
        localStorage.removeItem('refresh-token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Autenticação - Usar proxy para contornar CORS
export const login = async (username: string, password: string) => {
  console.log('📡 [API] Preparando login...', { username, api_url: API_BASE_URL });
  
  try {
    // Tentar via proxy do Next.js (contorna CORS)
    console.log('📤 [API] Tentando via proxy /api/proxy-login');
    const proxyResponse = await axios.post('/api/proxy-login', {
      username,
      password
    });
    
    console.log('📥 [API] Resposta do proxy recebida:', { 
      status: proxyResponse.status,
      has_access_token: !!proxyResponse.data.access_token
    });
    
    // Salvar refresh token
    if (proxyResponse.data.refresh_token) {
      localStorage.setItem('refresh-token', proxyResponse.data.refresh_token);
      console.log('💾 [API] Refresh token salvo');
    }
    
    return proxyResponse.data;
  } catch (proxyError: any) {
    console.error('❌ [API] Erro no proxy, tentando direto...', proxyError.message);
    
    // Fallback: tentar direto (pode falhar por CORS)
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    console.log('📤 [API] Enviando requisição direta para /api/v1/auth/login');
    
    const response = await api.post('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    console.log('📥 [API] Resposta recebida:', { 
      status: response.status,
      has_access_token: !!response.data.access_token,
      has_refresh_token: !!response.data.refresh_token
    });
    
    // Salvar refresh token
    if (response.data.refresh_token) {
      localStorage.setItem('refresh-token', response.data.refresh_token);
      console.log('💾 [API] Refresh token salvo');
    }
    
    return response.data;
  }
};

export const signup = async (data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await api.post('/api/v1/users', data, { headers });
  return response.data;
};

export const logout = async () => {
  try {
    await api.post('/api/v1/auth/logout');
  } catch (error) {
    console.error('Erro no logout:', error);
  } finally {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh-token');
  }
};

export const getCurrentUser = async () => {
  const response = await api.get('/api/v1/auth/me');
  return response.data;
};

// Novos endpoints para seleção de BU/Empresa
export const getUserBusinessUnits = async () => {
  const token = localStorage.getItem('token');
  
  if (!token) {
    console.error('❌ [API] Token não encontrado no localStorage');
    throw new Error('Token não encontrado');
  }
  
  try {
    // Tentar via proxy do Next.js (contorna CORS)
    console.log('📡 [API] Buscando business units via proxy...');
    const proxyResponse = await axios.get('/api/proxy-business-units', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    console.log('✅ [API] Business units carregadas via proxy');
    return proxyResponse.data;
  } catch (proxyError: any) {
    console.error('❌ [API] Erro no proxy, tentando direto...', proxyError.message);
    
    // Fallback: tentar direto (pode falhar por CORS)
    const response = await api.get('/api/v1/auth/user-business-units');
    return response.data;
  }
};

export const selectBusinessUnit = async (businessUnitId: string) => {
  const token = localStorage.getItem('token');
  
  if (!token) {
    console.error('❌ [API] Token não encontrado para seleção de BU');
    throw new Error('Token não encontrado');
  }
  
  try {
    // Tentar via proxy do Next.js (contorna CORS e problemas de roteamento)
    console.log('📡 [API] Selecionando BU via proxy...', businessUnitId);
    const proxyResponse = await axios.post('/api/proxy-select-bu', {
      business_unit_id: businessUnitId
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    console.log('✅ [API] BU selecionada via proxy');
    return proxyResponse.data;
  } catch (proxyError: any) {
    console.error('❌ [API] Erro no proxy de seleção, tentando direto...', proxyError.message);
    
    // Fallback: tentar direto (pode falhar por CORS ou 404)
    const response = await api.post('/api/v1/auth/select-business-unit', {
      business_unit_id: businessUnitId
    });
    return response.data;
  }
};

// Grupos de Contas
export const getAccountGroups = async () => {
  const response = await api.get('/api/v1/financial/account-groups');
  return response.data;
};

export const createAccountGroup = async (data: any) => {
  const response = await api.post('/api/v1/financial/account-groups', data);
  return response.data;
};

// Subgrupos de Contas
export const getAccountSubgroups = async (groupId?: string, token?: string) => {
  const params = groupId ? { group_id: groupId } : {};
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get('/api/v1/financial/account-subgroups', { params, headers });
  return response.data;
};

export const createAccountSubgroup = async (data: any) => {
  const response = await api.post('/api/v1/financial/account-subgroups', data);
  return response.data;
};

// Contas
export const getAccounts = async (subgroupId?: string, accountType?: string, token?: string) => {
  const params: any = {};
  if (subgroupId) params.subgroup_id = subgroupId;
  if (accountType) params.account_type = accountType;
  
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await api.get('/api/v1/financial/accounts', { params, headers });
  return response.data;
};

export const createAccount = async (data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.post('/api/v1/financial/accounts', data, { headers });
  return response.data;
};

export const updateAccount = async (id: string, data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.put(`/api/v1/financial/accounts/${id}`, data, { headers });
  return response.data;
};

export const deleteAccount = async (id: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.delete(`/api/v1/financial/accounts/${id}`, { headers });
  return response.data;
};

// Subgrupos (alias para getAccountSubgroups)
export const getSubgroups = async (groupId?: string, token?: string) => {
  return getAccountSubgroups(groupId, token);
};

// Transações
export const getTransactions = async (params?: {
  start_date?: string;
  end_date?: string;
  account_id?: string;
  transaction_type?: string;
  is_forecast?: boolean;
}, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get('/api/v1/financial/transactions', { params, headers });
  return response.data;
};

export const createTransaction = async (data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.post('/api/v1/financial/transactions', data, { headers });
  return response.data;
};

// Fluxo de Caixa
export const getCashFlow = async (params: {
  start_date: string;
  end_date: string;
  period_type?: string;
  business_unit_id?: string;
}, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get('/api/v1/financial/cash-flow', { params, headers });
  return response.data;
};

// Contas Bancárias
export const getBankAccounts = async () => {
  const response = await api.get('/api/v1/financial/bank-accounts');
  return response.data;
};

export const createBankAccount = async (data: any) => {
  const response = await api.post('/api/v1/financial/bank-accounts', data);
  return response.data;
};

// Usuários
export const getUsers = async (token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get('/api/v1/users', { headers });
  return response.data;
};

export const createUser = async (data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.post('/api/v1/users', data, { headers });
  return response.data;
};

export const deleteUser = async (id: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.delete(`/api/v1/users/${id}`, { headers });
  return response.data;
};

// Tenants
export const getTenants = async (token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get('/api/v1/tenants', { headers });
  return response.data;
};

export const createTenant = async (data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.post('/api/v1/tenants', data, { headers });
  return response.data;
};

export const deleteTenant = async (id: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.delete(`/api/v1/tenants/${id}`, { headers });
  return response.data;
};

// Previsões
export const getForecasts = async (token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get('/api/v1/financial/forecasts', { headers });
  return response.data;
};

export const createForecast = async (data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.post('/api/v1/financial/forecasts', data, { headers });
  return response.data;
};

export const updateForecast = async (id: string, data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.put(`/api/v1/financial/forecasts/${id}`, data, { headers });
  return response.data;
};

export const deleteForecast = async (id: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.delete(`/api/v1/financial/forecasts/${id}`, { headers });
  return response.data;
};

// Grupos
export const getGroups = async (token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get('/api/v1/financial/groups', { headers });
  return response.data;
};

export const createGroup = async (data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.post('/api/v1/financial/groups', data, { headers });
  return response.data;
};

export const updateGroup = async (id: string, data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.put(`/api/v1/financial/groups/${id}`, data, { headers });
  return response.data;
};

export const deleteGroup = async (id: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.delete(`/api/v1/financial/groups/${id}`, { headers });
  return response.data;
};

// Subgrupos (funções adicionais)
export const createSubgroup = async (data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.post('/api/v1/financial/account-subgroups', data, { headers });
  return response.data;
};

export const updateSubgroup = async (id: string, data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.put(`/api/v1/financial/account-subgroups/${id}`, data, { headers });
  return response.data;
};

export const deleteSubgroup = async (id: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.delete(`/api/v1/financial/account-subgroups/${id}`, { headers });
  return response.data;
};

// Transações (funções adicionais)
export const updateTransaction = async (id: string, data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.put(`/api/v1/financial/transactions/${id}`, data, { headers });
  return response.data;
};

export const deleteTransaction = async (id: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.delete(`/api/v1/financial/transactions/${id}`, { headers });
  return response.data;
};

// Importação CSV
export const importCsv = async (file: File, table: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('table', table);
  
  const response = await api.post('/api/v1/csv/import-csv', formData, { 
    headers: {
      ...headers,
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};

// Relatórios
export const getCashFlowReport = async (params: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get('/api/v1/financial/cash-flow-report', { 
    params,
    headers 
  });
  return response.data;
};

// Usuários
export const updateUser = async (id: string, data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.put(`/api/v1/users/${id}`, data, { headers });
  return response.data;
};

// Tenants
export const updateTenant = async (id: string, data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.put(`/api/v1/tenants/${id}`, data, { headers });
  return response.data;
};

// Business Units
export const getBusinessUnits = async (tenantId?: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const params: any = {};
  if (tenantId) {
    params.tenant_id = tenantId;
  }
  
  const response = await api.get('/api/v1/business-units', { 
    headers,
    params
  });
  return response.data;
};

export const createBusinessUnit = async (data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.post('/api/v1/business-units', data, { headers });
  return response.data;
};

export const updateBusinessUnit = async (id: string, data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.put(`/api/v1/business-units/${id}`, data, { headers });
  return response.data;
};

export const deleteBusinessUnit = async (id: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.delete(`/api/v1/business-units/${id}`, { headers });
  return response.data;
};

// ============================================================================
// PERMISSÕES DE USUÁRIO
// ============================================================================

// Permissões de Empresa (Tenant)
export const getUserTenantPermissions = async (userId: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get(`/api/v1/permissions/tenants/${userId}`, { headers });
  return response.data;
};

export const createUserTenantPermission = async (data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.post('/api/v1/permissions/tenants', data, { headers });
  return response.data;
};

export const updateUserTenantPermission = async (permissionId: string, data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.put(`/api/v1/permissions/tenants/${permissionId}`, data, { headers });
  return response.data;
};

export const deleteUserTenantPermission = async (permissionId: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.delete(`/api/v1/permissions/tenants/${permissionId}`, { headers });
  return response.data;
};

// Permissões de Business Unit
export const getUserBusinessUnitPermissions = async (userId: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get(`/api/v1/permissions/business-units/${userId}`, { headers });
  return response.data;
};

export const createUserBusinessUnitPermission = async (data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.post('/api/v1/permissions/business-units', data, { headers });
  return response.data;
};

export const updateUserBusinessUnitPermission = async (permissionId: string, data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.put(`/api/v1/permissions/business-units/${permissionId}`, data, { headers });
  return response.data;
};

export const deleteUserBusinessUnitPermission = async (permissionId: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.delete(`/api/v1/permissions/business-units/${permissionId}`, { headers });
  return response.data;
};

// Consulta de permissões do usuário atual
export const getMyAccess = async (token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get('/api/v1/permissions/my-access', { headers });
  return response.data;
};

export const getUserInfo = async (): Promise<any> => {
  const response = await api.get('/api/v1/auth/user-info');
  return response.data;
};

export const needsBusinessUnitSelection = async (): Promise<any> => {
  const response = await api.get('/api/v1/auth/needs-business-unit-selection');
  return response.data;
};

export const getPermissions = async (): Promise<any> => {
  const response = await api.get('/api/v1/permissions');
  return response.data;
};

export const getUserPermissions = async (userId: string, businessUnitId: string): Promise<any> => {
  const response = await api.get(`/api/v1/permissions/users/${userId}/business-units/${businessUnitId}`);
  return response.data;
};

export const updateUserPermissions = async (userId: string, businessUnitId: string, permissions: any[]): Promise<any> => {
  const response = await api.put(`/api/v1/permissions/users/${userId}/business-units/${businessUnitId}`, {
    permissions
  });
  return response.data;
};

// ============================================================================
// FUNÇÕES DO PLANO DE CONTAS
// ============================================================================

// Função para obter hierarquia completa do plano de contas
export const getChartAccountsHierarchy = async (token?: string) => {
  try {
    const response = await api.get('/api/v1/chart-accounts/hierarchy');
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Erro ao buscar hierarquia do plano de contas');
  }
};

// Função para obter grupos do plano de contas
export const getChartAccountGroups = async (token?: string) => {
  try {
    const response = await api.get('/api/v1/chart-accounts/groups');
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Erro ao buscar grupos');
  }
};

// Função para obter subgrupos do plano de contas
export const getChartAccountSubgroups = async (groupId?: string, token?: string) => {
  try {
    const params: any = {};
    if (groupId) {
      params.group_id = groupId;
    }

    const response = await api.get('/api/v1/chart-accounts/subgroups', { params });
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Erro ao buscar subgrupos');
  }
};

// Função para obter contas do plano de contas
export const getChartAccounts = async (subgroupId?: string, groupId?: string, token?: string) => {
  try {
    const params: any = {};
    if (subgroupId) {
      params.subgroup_id = subgroupId;
    }
    if (groupId) {
      params.group_id = groupId;
    }

    const response = await api.get('/api/v1/chart-accounts/accounts', { params });
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Erro ao buscar contas');
  }
};

// Função para importar plano de contas do CSV
export const importChartAccounts = async (file: File, token?: string) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const headers: any = {
      'Content-Type': 'multipart/form-data'
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await axios.post(
      `${API_BASE_URL}/api/v1/chart-accounts/import`,
      formData,
      { headers }
    );
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Erro ao importar plano de contas');
  }
};

// ============================================================================
// IMPORTAÇÃO GOOGLE SHEETS
// ============================================================================

// Informações da planilha de exemplo
export const getSampleSpreadsheetInfo = async (token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get('/api/v1/import/google-sheets/sample', { headers });
  return response.data;
};

// Validar estrutura de dados de uma planilha Google Sheets
export const validateGoogleSheetsData = async (spreadsheetId: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.post('/api/v1/import/google-sheets/validate', null, {
    params: { spreadsheet_id: spreadsheetId },
    headers
  });
  return response.data;
};

// Importar dados de uma planilha Google Sheets
export const importFromGoogleSheets = async (data: {
  spreadsheet_id: string;
  import_type?: string;
  validate_only?: boolean;
}, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.post('/api/v1/import/google-sheets', data, { headers });
  return response.data;
};

// Obter status de uma importação
export const getImportStatus = async (importId: string, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await api.get(`/api/v1/import/status/${importId}`, { headers });
  return response.data;
};

export default api;
