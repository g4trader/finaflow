/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    appDir: false,
  },
  async rewrites() {
    return [
      {
        source: '/:path*',
        destination: '/',
      },
    ];
  },
  // Configurações para Vercel
  output: 'standalone',
  poweredByHeader: false,
  generateEtags: false,
}

module.exports = nextConfig
