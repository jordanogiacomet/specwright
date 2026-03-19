export const localeDefinitions = [
  { code: "en", label: "English" },
  { code: "pt", label: "Portuguese" },
] as const;

export type AppLocale = (typeof localeDefinitions)[number]["code"];

export type LocalizedTextValue = Partial<Record<AppLocale, string>>;
export type LocalizedTextPatch = Partial<Record<AppLocale, string | null>>;

export const supportedLocales = localeDefinitions.map(
  ({ code }) => code,
) as AppLocale[];

export const defaultLocale: AppLocale = "en";

export const localeFallbacks: Record<AppLocale, readonly AppLocale[]> = {
  en: [],
  pt: ["en"],
};

export const localeConfig = {
  locales: localeDefinitions,
  defaultLocale,
  fallbackRules: localeFallbacks,
} as const;

export function isLocaleCode(value: unknown): value is AppLocale {
  return (
    typeof value === "string" && supportedLocales.includes(value as AppLocale)
  );
}

function normalizePathname(pathname: string): string {
  if (!pathname) {
    return "/";
  }

  const normalizedPathname = pathname.startsWith("/") ? pathname : `/${pathname}`;
  const searchIndex = normalizedPathname.search(/[?#]/);
  const pathnameOnly =
    searchIndex === -1
      ? normalizedPathname
      : normalizedPathname.slice(0, searchIndex);

  if (pathnameOnly === "/") {
    return pathnameOnly;
  }

  return pathnameOnly.replace(/\/+$/, "") || "/";
}

export function getPathnameLocale(pathname: string): AppLocale | null {
  const [firstSegment] = normalizePathname(pathname).split("/").filter(Boolean);

  return isLocaleCode(firstSegment) ? firstSegment : null;
}

export function getPathnameWithoutLocale(pathname: string): string {
  const segments = normalizePathname(pathname).split("/").filter(Boolean);

  if (segments.length === 0) {
    return "/";
  }

  const remainingSegments = isLocaleCode(segments[0])
    ? segments.slice(1)
    : segments;

  return remainingSegments.length > 0 ? `/${remainingSegments.join("/")}` : "/";
}

export function getLocalizedPathname(
  pathname: string,
  locale: AppLocale,
): string {
  const pathnameWithoutLocale = getPathnameWithoutLocale(pathname);

  return pathnameWithoutLocale === "/"
    ? `/${locale}`
    : `/${locale}${pathnameWithoutLocale}`;
}

export function getLocaleFallbackChain(
  locale: AppLocale,
  fallbackLocale: AppLocale = defaultLocale,
): AppLocale[] {
  const chain = [locale, ...localeFallbacks[locale], fallbackLocale];

  return chain.filter((value, index) => chain.indexOf(value) === index);
}

export function getAvailableLocales(
  ...localizedValues: LocalizedTextValue[]
): AppLocale[] {
  const availableLocales = new Set<AppLocale>();

  for (const localizedValue of localizedValues) {
    for (const locale of supportedLocales) {
      const value = localizedValue[locale];

      if (typeof value === "string" && value.trim()) {
        availableLocales.add(locale);
      }
    }
  }

  return supportedLocales.filter((locale) => availableLocales.has(locale));
}

export function resolveLocalizedText(
  localizedValue: LocalizedTextValue,
  locale: AppLocale,
  fallbackLocale: AppLocale = defaultLocale,
): { locale: AppLocale; value: string; fallbackChain: AppLocale[] } | null {
  const fallbackChain = getLocaleFallbackChain(locale, fallbackLocale);

  for (const candidateLocale of fallbackChain) {
    const value = localizedValue[candidateLocale];

    if (typeof value === "string" && value.trim()) {
      return {
        locale: candidateLocale,
        value,
        fallbackChain,
      };
    }
  }

  return null;
}
