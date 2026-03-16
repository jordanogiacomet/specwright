import type { ReactNode } from "react";

import Layout from "@/components/Layout";

type Props = {
  children: ReactNode;
};

export default function AppLayout({ children }: Props) {
  return <Layout>{children}</Layout>;
}
