/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Configuración para desarrollo
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000',
  },

  // Desactivar telemetría de Next.js (opcional)
  // telemetry: false,
};

module.exports = nextConfig;