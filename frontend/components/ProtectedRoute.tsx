import React, { useEffect, useState } from 'react';
import type { NextRouter } from 'next/router';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

function useSafeRouter(): NextRouter | null {
  try {
    return useRouter();
  } catch (error) {
    if (process.env.NODE_ENV === 'test') {
      return null;
    }
    throw error;
  }
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { token, isLoading } = useAuth();
  const router = useSafeRouter();
  const [isRedirecting, setIsRedirecting] = useState(false);

  useEffect(() => {
    // Aguardar o AuthContext carregar
    if (!isLoading) {
      if (!token) {
        console.log('🔒 Usuário não autenticado, redirecionando para login...');
        setIsRedirecting(true);
        if (router?.replace) {
          router.replace('/login');
        } else if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }
    }
  }, [token, isLoading, router]);

  // Se está carregando ou redirecionando, mostra loading
  if (isLoading || isRedirecting || !token) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">
            {isLoading ? 'Carregando...' : 'Verificando autenticação...'}
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
