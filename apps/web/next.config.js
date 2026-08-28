/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "export",
  turbopack: {
    root: __dirname,
  },
};

module.exports = nextConfig;
