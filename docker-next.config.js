/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    ignoreBuildErrors: true,
  },
  reactStrictMode: true,
  images: {
    unoptimized: true,
  },
  // This is important for the standalone output to find assets correctly
  assetPrefix: '',
}

module.exports = nextConfig; 