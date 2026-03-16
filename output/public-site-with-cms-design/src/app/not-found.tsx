import Link from "next/link";

import { defaultLocale, getLocalePathname } from "@/lib/i18n";

export default function NotFoundPage() {
  return (
    <main className="site-main">
      <section className="home-placeholder">
        <p className="home-kicker">404 - page not found</p>
        <h1>Page not found</h1>
        <p>The requested route does not exist for this public site.</p>
        <p>
          Return to{" "}
          <Link href={getLocalePathname(defaultLocale)}>the default locale</Link>
          .
        </p>
      </section>
    </main>
  );
}
