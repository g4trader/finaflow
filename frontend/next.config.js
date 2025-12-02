/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // Configurações para Vercel
  poweredByHeader: false,
  generateEtags: false,
}

module.exports = nextConfig
