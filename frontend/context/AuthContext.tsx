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

// Função para definir cookie
const setCookie = (name: string, value: string, days: number) => {
  if (typeof window !== 'undefined') {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;secure;samesite=strict`;
  }
};

// Função para obter cookie
const getCookie = (name: string): string | null => {
  if (typeof window !== 'undefined') {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
  }
  return null;
};

// Função para remover cookie
const removeCookie = (name: string) => {
  if (typeof window !== 'undefined') {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
  }
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
        // Tentar localStorage primeiro (para compatibilidade)
        let stored = localStorage.getItem('token');
        
        // Se não tem no localStorage, tentar cookie
        if (!stored) {
          stored = getCookie('auth-token');
        }
        
        if (stored) {
          setToken(stored);
          const decoded: any = jwtDecode(stored);
          setRole(decoded.role);
          setTenantId(decoded.tenant_id || null);
          
          // Sincronizar com cookie para middleware
          setCookie('auth-token', stored, 7);
        }
      } catch (error) {
        console.error('Erro ao carregar token:', error);
        // Limpar tokens inválidos
        localStorage.removeItem('token');
        removeCookie('auth-token');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const data = await apiLogin(username, password);
      setToken(data.access_token);
      
      // Salvar em localStorage e cookie
      localStorage.setItem('token', data.access_token);
      setCookie('auth-token', data.access_token, 7);
      
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
    setRole(null);
    setTenantId(null);
    
    // Limpar localStorage e cookie
    localStorage.removeItem('token');
    removeCookie('auth-token');
  };

  return (
    <AuthContext.Provider value={{ token, role, tenantId, login, signup, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
