import type { NextConfig } from "next";
import { supportedLocales } from "./src/lib/i18n";

const cdnAssetPrefix = process.env.NEXT_PUBLIC_CDN_URL?.replace(/\/$/, "");
const localizedRootPathSource = `/:locale(${supportedLocales.join("|")})`;

const immutableAssetHeaders = [
  {
    key: "Cache-Control",
    value: "public, max-age=31536000, s-maxage=31536000, immutable",
  },
];

const edgeCachedPageHeaders = [
  {
    key: "Cache-Control",
    value: "public, max-age=0, s-maxage=300, stale-while-revalidate=86400",
  },
];

const optimizedImageHeaders = [
  {
    key: "Cache-Control",
    value: "public, max-age=0, s-maxage=86400, stale-while-revalidate=604800",
  },
];

const nextConfig: NextConfig = {
  assetPrefix: cdnAssetPrefix || undefined,
  async headers() {
    return [
      {
        source: "/_next/static/:path*",
        headers: immutableAssetHeaders,
      },
      {
        source: "/_next/image",
        headers: optimizedImageHeaders,
      },
      {
        source: "/",
        headers: edgeCachedPageHeaders,
      },
      {
        source: localizedRootPathSource,
        headers: edgeCachedPageHeaders,
      },
    ];
  },
};

export default nextConfig;
