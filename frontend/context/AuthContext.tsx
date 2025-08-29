import React, { createContext, useState, useEffect, ReactNode, useContext } from 'react';
import jwtDecode from 'jwt-decode';
import { login as apiLogin, signup as apiSignup } from '../services/api';
import Cookies from 'js-cookie';

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
        // Tentar localStorage primeiro (para compatibilidade)
        let stored = localStorage.getItem('token');
        
        // Se não tem no localStorage, tentar cookie
        if (!stored) {
          stored = Cookies.get('auth-token') || null;
        }
        
        if (stored) {
          setToken(stored);
          const decoded: any = jwtDecode(stored);
          setRole(decoded.role);
          setTenantId(decoded.tenant_id || null);
          
          // Sincronizar com cookie para middleware
          Cookies.set('auth-token', stored, { expires: 7, secure: true, sameSite: 'strict' });
        }
      } catch (error) {
        console.error('Erro ao carregar token:', error);
        // Limpar tokens inválidos
        localStorage.removeItem('token');
        Cookies.remove('auth-token');
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
      Cookies.set('auth-token', data.access_token, { expires: 7, secure: true, sameSite: 'strict' });
      
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
    Cookies.remove('auth-token');
  };

  return (
    <AuthContext.Provider value={{ token, role, tenantId, login, signup, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
