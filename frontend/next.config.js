/** @type {import('next').NextConfig} */
const backendUrl =
  process.env.BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Configurações de deploy
  poweredByHeader: false,
  generateEtags: false,

  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${backendUrl.replace(/\/$/, '')}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
