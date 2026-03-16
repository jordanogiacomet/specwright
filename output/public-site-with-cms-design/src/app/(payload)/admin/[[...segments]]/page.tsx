import type { Metadata } from "next";
import { generatePageMetadata, RootPage } from "@payloadcms/next/views";

import config from "@payload-config";

import { importMap } from "../importMap.js";

type AdminPageProps = {
  params: Promise<{
    segments?: string[];
  }>;
  searchParams: Promise<{
    [key: string]: string | string[];
  }>;
};

const configPromise = Promise.resolve(config);

function normalizeParams(params: AdminPageProps["params"]) {
  return params.then(({ segments = [] }) => ({ segments }));
}

export async function generateMetadata({
  params,
  searchParams,
}: AdminPageProps): Promise<Metadata> {
  return generatePageMetadata({
    config: configPromise,
    params: normalizeParams(params),
    searchParams,
  });
}

export default async function Page({ params, searchParams }: AdminPageProps) {
  return RootPage({
    config: configPromise,
    importMap,
    params: normalizeParams(params),
    searchParams,
  });
}
