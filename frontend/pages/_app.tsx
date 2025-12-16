import type { AppProps } from 'next/app';
import { AuthProvider } from '../context/AuthContext';
import '../styles/globals.css';
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import React from 'react';
import { useAuth } from '../context/AuthContext';

// Componente para proteção de rotas
function RouteProtection({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [mounted, setMounted] = React.useState(false);
  
  // Garantir que só execute no cliente
  React.useEffect(() => {
    setMounted(true);
  }, []);
  
  // Se ainda não montou no cliente, mostrar loading
  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando...</p>
        </div>
      </div>
    );
  }
  
  return <RouteProtectionInner>{children}</RouteProtectionInner>;
}

// Componente interno que usa hooks do AuthContext
function RouteProtectionInner({ children }: { children: React.ReactNode }) {
  const [isClient, setIsClient] = React.useState(false);
  const { token, isLoading } = useAuth();
  const router = useRouter();
  
  // Garantir que só execute no cliente
  useEffect(() => {
    setIsClient(true);
  }, []);
  
  // Rotas que precisam de autenticação
  const protectedRoutes = [
    '/dashboard',
    '/dashboard-operational',
    '/accounts',
    // '/transactions',  // Temporariamente removido para teste
    '/groups',
    '/subgroups',
    '/users',
    '/forecast',
    '/reports',
    '/settings',
    '/csv-import'
  ];
  
  // Rotas públicas
  const publicRoutes = ['/login', '/signup', '/forgot-password', '/'];
  
  useEffect(() => {
    // Só executar no cliente e após carregar
    if (!isClient || isLoading || typeof window === 'undefined') {
      return;
    }
    
    const currentPath = router.pathname;
    const isProtectedRoute = protectedRoutes.some(route => currentPath.startsWith(route));
    
    // Se é rota protegida e não tem token, redirecionar para login
    if (isProtectedRoute && !token) {
      console.log(`🔒 RouteProtection: Redirecionando ${currentPath} para login`);
      router.replace('/login');
      return;
    }
    
    // Se tem token e está tentando acessar login/signup, redirecionar para dashboard
    if (token && (currentPath === '/login' || currentPath === '/signup')) {
      console.log(`🔄 RouteProtection: Usuário autenticado tentando acessar ${currentPath}, redirecionando para dashboard`);
      router.replace('/dashboard');
      return;
    }
  }, [token, isLoading, router, isClient]);
  
  // Se está carregando ou ainda não está no cliente, mostrar loading
  if (!isClient || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando...</p>
        </div>
      </div>
    );
  }
  
  return <>{children}</>;
}

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <RouteProtection>
        <Component {...pageProps} />
      </RouteProtection>
    </AuthProvider>
  );
}

export default MyApp;
