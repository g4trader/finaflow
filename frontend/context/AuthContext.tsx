import React, { createContext, useState, useEffect, ReactNode, useContext } from 'react';
import jwtDecode from 'jwt-decode';
import { login as apiLogin, signup as apiSignup } from '../services/api';

interface AuthContextType {
  token: string | null;
  role: string | null;
  tenantId: string | null;
  login: (username: string, password: string) => Promise<void>;
  signup: (data: any) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

export const AuthContext = createContext<AuthContextType>({} as AuthContextType);

// Hook personalizado para usar o contexto de autenticação
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Verificar se estamos no cliente (browser)
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem('token');
        if (stored) {
          setToken(stored);
          const decoded: any = jwtDecode(stored);
          setRole(decoded.role);
          setTenantId(decoded.tenant_id || null);
        }
      } catch (error) {
        console.error('Erro ao carregar token do localStorage:', error);
        localStorage.removeItem('token');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const data = await apiLogin(username, password);
      setToken(data.access_token);
      localStorage.setItem('token', data.access_token);
      const decoded: any = jwtDecode(data.access_token);
      setRole(decoded.role);
      setTenantId(decoded.tenant_id || null);
    } catch (error) {
      console.error('Erro no login:', error);
      throw error;
    }
  };

  const signup = async (data: any) => {
    const response = await apiSignup(data, token ?? undefined);
    return response;
  };

  const logout = () => {
    setToken(null);
    localStorage.removeItem('token');
    setRole(null);
    setTenantId(null);
  };

  return (
    <AuthContext.Provider value={{ token, role, tenantId, login, signup, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
