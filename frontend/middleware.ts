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

// Rotas públicas
const publicRoutes = [
  '/login',
  '/signup',
  '/forgot-password',
  '/'
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Verificar se é uma rota protegida
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
  const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route));
  
  // Verificar token no cookie
  const token = request.cookies.get('auth-token')?.value;
  
  // Se é rota protegida e não tem token, redirecionar para login
  if (isProtectedRoute && !token) {
    console.log(`🔒 Acesso negado a ${pathname} - redirecionando para login`);
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  // Se tem token e está tentando acessar login/signup, redirecionar para dashboard
  if (token && (pathname === '/login' || pathname === '/signup')) {
    console.log(`🔄 Usuário autenticado tentando acessar ${pathname} - redirecionando para dashboard`);
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }
  
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
