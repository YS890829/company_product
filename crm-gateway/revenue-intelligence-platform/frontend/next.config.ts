import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: '/ai-agents',
        destination: '/agents',
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
