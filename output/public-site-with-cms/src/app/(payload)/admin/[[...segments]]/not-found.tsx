import config from "@payload-config";
import { NotFoundPage } from "@payloadcms/next/views";

import { importMap } from "../../importMap";

type Args = {
  params?: Promise<{ segments: string[] }>;
  searchParams?: Promise<{ [key: string]: string | string[] }>;
};

const Page = ({ params, searchParams }: Args) =>
  NotFoundPage({
    config,
    importMap,
    params: params ?? Promise.resolve({ segments: [] }),
    searchParams: searchParams ?? Promise.resolve({}),
  });

export default Page;
