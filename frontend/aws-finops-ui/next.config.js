/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['xterm'],
  webpack: (config) => {
    // Avoid SSR issues with modules that rely on browser APIs
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
      child_process: false,
    };
    return config;
  },
  // Handle CSS imports normally - don't use custom CSS configuration
  // which would require style-loader and css-loader
  
  // Add API route rewrites to proxy requests to the Python backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5001/api/:path*'
      }
    ];
  }
};

module.exports = nextConfig; 