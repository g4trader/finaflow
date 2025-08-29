import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Rotas que precisam de autenticação
const protectedRoutes = [
  '/dashboard',
  '/accounts',
  '/transactions',
  '/groups',
  '/subgroups',
  '/users',
  '/forecast',
  '/reports',
  '/settings',
  '/csv-import'
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  console.log(`🔍 Middleware executando para: ${pathname}`);
  
  // Verificar se é uma rota protegida
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
  
  console.log(`🔒 Rota protegida: ${isProtectedRoute}`);
  
  // Verificar token no cookie ou header
  const token = request.cookies.get('auth-token')?.value || 
                request.headers.get('authorization')?.replace('Bearer ', '');
  
  console.log(`🔑 Token encontrado: ${!!token}`);
  
  // Se é rota protegida e não tem token, redirecionar para login
  if (isProtectedRoute && !token) {
    console.log(`🔒 Middleware: Acesso negado a ${pathname} - redirecionando para login`);
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  // Se tem token e está tentando acessar login/signup, redirecionar para dashboard
  if (token && (pathname === '/login' || pathname === '/signup')) {
    console.log(`🔄 Middleware: Usuário autenticado tentando acessar ${pathname} - redirecionando para dashboard`);
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }
  
  console.log(`✅ Middleware: Permitindo acesso a ${pathname}`);
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
