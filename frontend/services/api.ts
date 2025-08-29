import axios from 'axios';

// Build timestamp: 2025-08-29 12:15:00 - Forcing Vercel deploy
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Configuração do axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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

// Autenticação
export const login = async (username: string, password: string) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await api.post('/api/v1/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  
  // Salvar refresh token
  if (response.data.refresh_token) {
    localStorage.setItem('refresh-token', response.data.refresh_token);
  }
  
  return response.data;
};

export const signup = async (data: any, token?: string) => {
  const headers: any = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await api.post('/api/v1/auth/users', data, { headers });
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
export const getAccountSubgroups = async (groupId?: string) => {
  const params = groupId ? { group_id: groupId } : {};
  const response = await api.get('/api/v1/financial/account-subgroups', { params });
  return response.data;
};

export const createAccountSubgroup = async (data: any) => {
  const response = await api.post('/api/v1/financial/account-subgroups', data);
  return response.data;
};

// Contas
export const getAccounts = async (subgroupId?: string, accountType?: string) => {
  const params: any = {};
  if (subgroupId) params.subgroup_id = subgroupId;
  if (accountType) params.account_type = accountType;
  
  const response = await api.get('/api/v1/financial/accounts', { params });
  return response.data;
};

export const createAccount = async (data: any) => {
  const response = await api.post('/api/v1/financial/accounts', data);
  return response.data;
};

export const updateAccount = async (id: string, data: any) => {
  const response = await api.put(`/api/v1/financial/accounts/${id}`, data);
  return response.data;
};

export const deleteAccount = async (id: string) => {
  const response = await api.delete(`/api/v1/financial/accounts/${id}`);
  return response.data;
};

// Subgrupos (alias para getAccountSubgroups)
export const getSubgroups = async (groupId?: string) => {
  return getAccountSubgroups(groupId);
};

// Transações
export const getTransactions = async (params?: {
  start_date?: string;
  end_date?: string;
  account_id?: string;
  transaction_type?: string;
  is_forecast?: boolean;
}) => {
  const response = await api.get('/api/v1/financial/transactions', { params });
  return response.data;
};

export const createTransaction = async (data: any) => {
  const response = await api.post('/api/v1/financial/transactions', data);
  return response.data;
};

// Fluxo de Caixa
export const getCashFlow = async (params: {
  start_date: string;
  end_date: string;
  period_type?: string;
  business_unit_id?: string;
}) => {
  const response = await api.get('/api/v1/financial/cash-flow', { params });
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
export const getUsers = async () => {
  const response = await api.get('/api/v1/auth/users');
  return response.data;
};

export const createUser = async (data: any) => {
  const response = await api.post('/api/v1/auth/users', data);
  return response.data;
};

// Tenants
export const createTenant = async (data: any) => {
  const response = await api.post('/api/v1/auth/tenants', data);
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

export default api;
