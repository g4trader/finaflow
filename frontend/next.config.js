/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Removendo configurações experimentais problemáticas
  // experimental: {
  //   appDir: false,
  // },
  // env: {
  //   CUSTOM_KEY: process.env.CUSTOM_KEY,
  // },
}

module.exports = nextConfig
