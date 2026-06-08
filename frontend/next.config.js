/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    NEXT_PUBLIC_WS_URL:  process.env.NEXT_PUBLIC_WS_URL  || "ws://localhost:8000",
  },
  webpack: (config) => {
    // face-api.js uses dynamic require internally — suppress the noisy warning
    config.ignoreWarnings = [
      { module: /@vladmandic\/face-api/ },
    ]
    return config
  },
}

module.exports = nextConfig
