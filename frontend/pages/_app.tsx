import type { AppProps } from 'next/app';
import { AuthProvider } from '../context/AuthContext';
import '../styles/globals.css';
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

// Componente para proteção de rotas
function RouteProtection({ children }: { children: React.ReactNode }) {
  const { token, isLoading } = useAuth();
  const router = useRouter();
  
  // Rotas que precisam de autenticação
  const protectedRoutes = [
    '/dashboard',
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
    if (!isLoading) {
      const currentPath = router.pathname;
      const isProtectedRoute = protectedRoutes.some(route => currentPath.startsWith(route));
      const isPublicRoute = publicRoutes.some(route => currentPath.startsWith(route));
      
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
    }
  }, [token, isLoading, router]);
  
  // Se está carregando, mostrar loading
  if (isLoading) {
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
