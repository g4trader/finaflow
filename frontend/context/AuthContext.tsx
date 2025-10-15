import React, { createContext, useState, useEffect, ReactNode, useContext } from 'react';
import jwtDecode from 'jwt-decode';
import { login as apiLogin, signup as apiSignup, needsBusinessUnitSelection as checkNeedsBusinessUnitSelection } from '../services/api';

interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  tenant_id: string;
  business_unit_id?: string;
  department_id?: string;
}

interface AuthContextType {
  token: string | null;
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  signup: (data: any) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  refreshToken: () => Promise<void>;
  role: string | null;
  tenantId: string | null;
  needsBusinessUnitSelection: boolean;
  setNeedsBusinessUnitSelection: (needs: boolean) => void;
}

export const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};

const setCookie = (name: string, value: string, days: number) => {
  if (typeof window !== 'undefined') {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;secure;samesite=strict`;
  }
};

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

const removeCookie = (name: string) => {
  if (typeof window !== 'undefined') {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
  }
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [needsBusinessUnitSelection, setNeedsBusinessUnitSelection] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        let stored = localStorage.getItem('token');
        if (!stored) {
          stored = getCookie('auth-token');
        }

        if (stored) {
          setToken(stored);
          const decoded: any = jwtDecode(stored);
          setUser({
            id: decoded.sub,
            username: decoded.username,
            email: decoded.email,
            first_name: decoded.first_name || '',
            last_name: decoded.last_name || '',
            role: decoded.role,
            tenant_id: decoded.tenant_id,
            business_unit_id: decoded.business_unit_id,
            department_id: decoded.department_id
          });
          setCookie('auth-token', stored, 7);
        }
      } catch (error) {
        console.error('Erro ao carregar token:', error);
        localStorage.removeItem('token');
        removeCookie('auth-token');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    try {
      console.log('🔐 [AuthContext] Iniciando login...', { username });
      
      // Limpar tokens antigos antes do login
      localStorage.removeItem('token');
      removeCookie('auth-token');
      
      console.log('📡 [AuthContext] Chamando API de login...');
      const data = await apiLogin(username, password);
      console.log('✅ [AuthContext] API retornou:', { 
        has_token: !!data.access_token,
        token_type: data.token_type,
        expires_in: data.expires_in
      });
      
      setToken(data.access_token);
      localStorage.setItem('token', data.access_token);
      setCookie('auth-token', data.access_token, 7);
      
      console.log('🔓 [AuthContext] Decodificando token...');
      const decoded: any = jwtDecode(data.access_token);
      console.log('✅ [AuthContext] Token decodificado:', {
        username: decoded.username,
        role: decoded.role,
        tenant_id: decoded.tenant_id,
        business_unit_id: decoded.business_unit_id
      });
      
      const userData = {
        id: decoded.sub,
        username: decoded.username,
        email: decoded.email,
        first_name: decoded.first_name || '',
        last_name: decoded.last_name || '',
        role: decoded.role,
        tenant_id: decoded.tenant_id,
        business_unit_id: decoded.business_unit_id,
        department_id: decoded.department_id
      };
      setUser(userData);
      console.log('👤 [AuthContext] Usuário configurado');
      
      // Verificar se o usuário precisa selecionar uma BU
      try {
        console.log('🔍 [AuthContext] Verificando necessidade de seleção de BU...');
        const needsSelection = await checkNeedsBusinessUnitSelection();
        console.log('📋 [AuthContext] Resposta da verificação de BU:', needsSelection);
        setNeedsBusinessUnitSelection(needsSelection.needs_selection);
      } catch (error) {
        console.error('⚠️ [AuthContext] Erro ao verificar necessidade de seleção de BU:', error);
        // Fallback: verificar se tem business_unit_id no token
        const needsBU = !decoded.business_unit_id;
        console.log(`📋 [AuthContext] Fallback - Precisa BU: ${needsBU}`);
        setNeedsBusinessUnitSelection(needsBU);
      }
      
      console.log('✅ [AuthContext] Login completo!');
    } catch (error) {
      console.error('❌ [AuthContext] Erro no login:', error);
      throw error;
    }
  };

  const signup = async (data: any) => {
    const response = await apiSignup(data, token ?? undefined);
    return response;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    removeCookie('auth-token');
  };

  const refreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh-token');
      if (!refreshToken) {
        throw new Error('Refresh token não encontrado');
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Falha ao renovar token');
      }

      const data = await response.json();
      setToken(data.access_token);
      localStorage.setItem('token', data.access_token);
      setCookie('auth-token', data.access_token, 7);
      
      const decoded: any = jwtDecode(data.access_token);
      setUser({
        id: decoded.sub,
        username: decoded.username,
        email: decoded.email,
        first_name: decoded.first_name || '',
        last_name: decoded.last_name || '',
        role: decoded.role,
        tenant_id: decoded.tenant_id,
        business_unit_id: decoded.business_unit_id,
        department_id: decoded.department_id
      });
    } catch (error) {
      console.error('Erro ao renovar token:', error);
      logout();
    }
  };

  return (
    <AuthContext.Provider value={{ 
      token, 
      user, 
      login, 
      signup, 
      logout, 
      isLoading, 
      refreshToken,
      role: user?.role || null,
      tenantId: user?.tenant_id || null,
      needsBusinessUnitSelection,
      setNeedsBusinessUnitSelection
    }}>
      {children}
    </AuthContext.Provider>
  );
};
