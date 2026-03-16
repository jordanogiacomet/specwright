import type { ReactNode } from "react";
import type { ServerFunctionClient } from "payload";
import { handleServerFunctions, metadata, RootLayout } from "@payloadcms/next/layouts";

import config from "@payload-config";

import { importMap } from "./admin/importMap.js";

export { metadata };

type Props = {
  children: ReactNode;
};

const configPromise = Promise.resolve(config);

const serverFunction: ServerFunctionClient = (args) =>
  handleServerFunctions({
    ...args,
    config: configPromise,
    importMap,
  });

export default async function Layout({ children }: Props) {
  return RootLayout({
    children,
    config: configPromise,
    importMap,
    serverFunction,
  });
}
