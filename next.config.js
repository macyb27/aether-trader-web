/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000',
  },
  // Skip static optimization for pages with client-side hooks
  experimental: {
    isrMemoryCacheSize: 0,
  },
};

module.exports = nextConfig;
