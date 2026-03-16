import { redirect } from "next/navigation";

import { defaultLocale, getLocalePathname } from "@/lib/i18n";

export default function HomePage() {
  redirect(getLocalePathname(defaultLocale));
}
