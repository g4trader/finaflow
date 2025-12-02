/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // Configurações para Vercel
  poweredByHeader: false,
  generateEtags: false,
  
  // Garantir que API routes funcionem corretamente
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
}

module.exports = nextConfig
