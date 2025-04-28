/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Allow images from TikTok domains
  images: {
    domains: ['p16-sign-va.tiktokcdn.com', 'p16-sign-sg.tiktokcdn.com', 'p16-sign.tiktokcdn-us.com'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.tiktokcdn.com',
      },
      {
        protocol: 'https',
        hostname: '**.tiktokcdn-us.com',
      },
    ],
  },
};

module.exports = nextConfig;
