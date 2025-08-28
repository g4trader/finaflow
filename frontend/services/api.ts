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

export default api;
