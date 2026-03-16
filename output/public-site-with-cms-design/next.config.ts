import { withPayload } from "@payloadcms/next/withPayload";
import type { NextConfig } from "next";

const publicCdnUrl =
  process.env.NEXT_PUBLIC_CDN_URL?.replace(/\/+$/, "") || undefined;
const publicAssetCacheControl =
  "public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800";

const nextConfig: NextConfig = {
  assetPrefix: publicCdnUrl,
  crossOrigin: publicCdnUrl ? "anonymous" : undefined,
  experimental: {
    reactCompiler: false,
  },
  async headers() {
    return [
      // Next applies immutable caching to `/_next/static` automatically.
      {
        source:
          "/:path*.(avif|css|gif|ico|jpg|jpeg|js|json|map|mp4|png|svg|txt|webmanifest|webm|webp|woff|woff2|xml)",
        headers: [
          {
            key: "Cache-Control",
            value: publicAssetCacheControl,
          },
        ],
      },
    ];
  },
};

export default withPayload(nextConfig);
