import { withPayload } from "@payloadcms/next/withPayload";
import type { NextConfig } from "next";

const IMMUTABLE_ASSET_CACHE_CONTROL = "public, max-age=31536000, immutable";
const PUBLIC_ROUTE_CACHE_CONTROL = "public, s-maxage=300, stale-while-revalidate=86400";
const PRIVATE_ROUTE_CACHE_CONTROL = "private, no-store, max-age=0";

const cdnAssetPrefix =
  process.env.NODE_ENV === "production"
    ? process.env.NEXT_PUBLIC_CDN_URL?.replace(/\/+$/, "")
    : undefined;

const nextConfig: NextConfig = {
  assetPrefix: cdnAssetPrefix,
  async headers() {
    return [
      {
        source: "/_next/static/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: IMMUTABLE_ASSET_CACHE_CONTROL,
          },
        ],
      },
      {
        source: "/",
        headers: [
          {
            key: "Cache-Control",
            value: PUBLIC_ROUTE_CACHE_CONTROL,
          },
        ],
      },
      {
        source: "/:locale(en|pt)",
        headers: [
          {
            key: "Cache-Control",
            value: PUBLIC_ROUTE_CACHE_CONTROL,
          },
        ],
      },
      {
        source: "/:locale(en|pt)/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: PUBLIC_ROUTE_CACHE_CONTROL,
          },
        ],
      },
      {
        source: "/admin",
        headers: [
          {
            key: "Cache-Control",
            value: PRIVATE_ROUTE_CACHE_CONTROL,
          },
        ],
      },
      {
        source: "/admin/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: PRIVATE_ROUTE_CACHE_CONTROL,
          },
        ],
      },
      {
        source: "/api/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: PRIVATE_ROUTE_CACHE_CONTROL,
          },
        ],
      },
    ];
  },
};

export default withPayload(nextConfig);
