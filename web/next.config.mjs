const backend = process.env.BACKEND_INTERNAL_URL || "http://localhost:8080";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [{ source: "/backend/:path*", destination: `${backend}/:path*` }];
  }
};

export default nextConfig;
