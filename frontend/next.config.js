/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // Configurações para Vercel
  poweredByHeader: false,
  generateEtags: false,
  
  // Desabilitar serverActions que pode causar problemas
  // experimental: {
  //   serverActions: {
  //     bodySizeLimit: '2mb',
  //   },
  // },
  
  // Garantir que não tente fazer SSR de páginas que usam browser APIs
  output: 'standalone',
}

module.exports = nextConfig
