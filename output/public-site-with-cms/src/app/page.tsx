import { redirect } from "next/navigation";

import { DEFAULT_LOCALE, getLocalizedPathname } from "@/lib/i18n";

export default function IndexPage() {
  redirect(getLocalizedPathname("/", DEFAULT_LOCALE));
}
