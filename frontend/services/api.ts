import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

export const login = async (username: string, password: string) => {
  const response = await api.post('/auth/login', { username, password });
  return response.data;
};

export const signup = async (data: any, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.post('/auth/signup', data, { headers });
  return response.data;
};

export const getCashFlowReport = async (groupBy: string = 'month', token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.get('/reports/cash-flow', {
    params: { group_by: groupBy },
    headers,
  });
  return response.data;
};

// User endpoints
export const getUsers = async (token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.get('/users', { headers });
  return response.data;
};

export const createUser = async (data: any, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.post('/users', data, { headers });
  return response.data;
};

export const updateUser = async (userId: string, data: any, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.put(`/users/${userId}`, data, { headers });
  return response.data;
};

export const deleteUser = async (userId: string, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.delete(`/users/${userId}`, { headers });
  return response.data;
};

// Group endpoints
export const getGroups = async (token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.get('/groups', { headers });
  return response.data;
};

export const createGroup = async (data: any, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.post('/groups', data, { headers });
  return response.data;
};

export const updateGroup = async (groupId: string, data: any, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.put(`/groups/${groupId}`, data, { headers });
  return response.data;
};

export const deleteGroup = async (groupId: string, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.delete(`/groups/${groupId}`, { headers });
  return response.data;
};

// Subgroup endpoints
export const getSubgroups = async (token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.get('/subgroups', { headers });
  return response.data;
};

export const createSubgroup = async (data: any, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.post('/subgroups', data, { headers });
  return response.data;
};

export const updateSubgroup = async (
  subgroupId: string,
  data: any,
  token?: string,
) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.put(`/subgroups/${subgroupId}`, data, { headers });
  return response.data;
};

export const deleteSubgroup = async (subgroupId: string, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.delete(`/subgroups/${subgroupId}`, { headers });
  return response.data;
};

// Account endpoints
export const getAccounts = async (token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.get('/accounts', { headers });
  return response.data;
};

export const createAccount = async (data: any, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.post('/accounts', data, { headers });
  return response.data;
};

export const updateAccount = async (accountId: string, data: any, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.put(`/accounts/${accountId}`, data, { headers });
  return response.data;
};

export const deleteAccount = async (accountId: string, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.delete(`/accounts/${accountId}`, { headers });
  return response.data;
};

// Transaction endpoints
export const getTransactions = async (token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.get('/transactions', { headers });
  return response.data;
};

export const createTransaction = async (data: any, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.post('/transactions', data, { headers });
  return response.data;
};

export const updateTransaction = async (
  transactionId: string,
  data: any,
  token?: string,
) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.put(`/transactions/${transactionId}`, data, { headers });
  return response.data;
};

export const deleteTransaction = async (transactionId: string, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.delete(`/transactions/${transactionId}`, { headers });
  return response.data;
};

// Forecast endpoints
export const getForecasts = async (token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.get('/forecast', { headers });
  return response.data;
};

export const createForecast = async (data: any, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.post('/forecast', data, { headers });
  return response.data;
};

export const updateForecast = async (
  forecastId: string,
  data: any,
  token?: string,
) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.put(`/forecast/${forecastId}`, data, { headers });
  return response.data;
};

export const deleteForecast = async (forecastId: string, token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.delete(`/forecast/${forecastId}`, { headers });
  return response.data;
};

// CSV import
export const importCsv = async (file: File, table: string, token?: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('table', table);
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
  const response = await api.post('/import-csv', formData, { headers });
  return response.data;
};

// Tenant endpoints
export const updateTenant = async (
  tenantId: string,
  data: any,
  token?: string,
) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.put(`/tenants/${tenantId}`, data, { headers });
  return response.data;
};

export default api;
