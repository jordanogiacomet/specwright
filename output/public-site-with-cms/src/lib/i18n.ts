import type {
  CollectionConfig,
  CollectionAfterReadHook,
  Field,
  LocalizationConfig,
  PayloadRequest,
} from "payload";

export const SUPPORTED_LOCALE_CODES = ["en", "pt"] as const;
export const DEFAULT_LOCALE = "en";
export const LOCALIZED_FIELD = {
  localized: true,
} as const;

export type SupportedLocaleCode = (typeof SUPPORTED_LOCALE_CODES)[number];
type LocaleDefinition = {
  code: SupportedLocaleCode;
  fallbackLocale?: SupportedLocaleCode[];
  label: string;
};
type LocaleMetadata = {
  availableLocales: string[];
  defaultLocale: string;
  fallbackLocale: false | string | string[];
  locale: "all" | string;
};

export const SUPPORTED_LOCALES: LocaleDefinition[] = [
  {
    code: "en",
    label: "English",
  },
  {
    code: "pt",
    label: "Portuguese",
    fallbackLocale: ["en"],
  },
];

const localeCodeSet = new Set<string>(SUPPORTED_LOCALE_CODES);

const normalizePathname = (pathname: string): string => {
  if (!pathname) {
    return "/";
  }

  const [withoutHash] = pathname.split("#");
  const [withoutSearch] = withoutHash.split("?");

  if (!withoutSearch.startsWith("/")) {
    return `/${withoutSearch}`;
  }

  return withoutSearch || "/";
};

const getPathSegments = (pathname: string): string[] =>
  normalizePathname(pathname)
    .split("/")
    .filter((segment) => segment.length > 0);

export const isSupportedLocale = (value: string): value is SupportedLocaleCode =>
  localeCodeSet.has(value);

export const resolveRouteLocale = (value?: string | null): SupportedLocaleCode => {
  if (typeof value === "string" && isSupportedLocale(value)) {
    return value;
  }

  return DEFAULT_LOCALE;
};

export const getLocaleFromPathname = (pathname: string): SupportedLocaleCode | null => {
  const [locale] = getPathSegments(pathname);

  if (locale && isSupportedLocale(locale)) {
    return locale;
  }

  return null;
};

export const stripLocaleFromPathname = (pathname: string): string => {
  const segments = getPathSegments(pathname);

  if (segments[0] && isSupportedLocale(segments[0])) {
    segments.shift();
  }

  return segments.length > 0 ? `/${segments.join("/")}` : "/";
};

export const getLocalizedPathname = (
  pathname: string,
  locale: SupportedLocaleCode,
): string => {
  const localizedPathname = stripLocaleFromPathname(pathname);

  if (localizedPathname === "/") {
    return `/${locale}`;
  }

  return `/${locale}${localizedPathname}`;
};

export const payloadLocalizationConfig: LocalizationConfig = {
  defaultLocale: DEFAULT_LOCALE,
  fallback: true,
  locales: [...SUPPORTED_LOCALES],
};

const resolveLocale = (req: PayloadRequest): LocaleMetadata["locale"] => {
  if (req.locale === "all") {
    return "all";
  }

  if (typeof req.locale === "string" && localeCodeSet.has(req.locale)) {
    return req.locale;
  }

  return DEFAULT_LOCALE;
};

const resolveConfiguredFallback = (
  locale: LocaleMetadata["locale"],
): LocaleMetadata["fallbackLocale"] => {
  if (locale === "all" || payloadLocalizationConfig.fallback !== true) {
    return false;
  }

  const localeConfig = SUPPORTED_LOCALES.find(({ code }) => code === locale);

  if (localeConfig?.fallbackLocale?.length) {
    return [...localeConfig.fallbackLocale];
  }

  return DEFAULT_LOCALE;
};

const resolveFallbackLocale = (
  req: PayloadRequest,
  locale: LocaleMetadata["locale"],
): LocaleMetadata["fallbackLocale"] => {
  const fallbackLocale = req.fallbackLocale;

  if (Array.isArray(fallbackLocale)) {
    const fallbackLocales = fallbackLocale.filter((code): code is SupportedLocaleCode =>
      localeCodeSet.has(code),
    );

    return fallbackLocales.length > 0 ? fallbackLocales : false;
  }

  if (typeof fallbackLocale === "string" && localeCodeSet.has(fallbackLocale)) {
    return fallbackLocale;
  }

  return resolveConfiguredFallback(locale);
};

export const buildLocaleMetadata = (req: PayloadRequest): LocaleMetadata => {
  const locale = resolveLocale(req);

  return {
    availableLocales: [...SUPPORTED_LOCALE_CODES],
    defaultLocale: DEFAULT_LOCALE,
    fallbackLocale: resolveFallbackLocale(req, locale),
    locale,
  };
};

export const localeMetadataField: Field = {
  name: "localeMeta",
  type: "group",
  virtual: true,
  admin: {
    position: "sidebar",
    readOnly: true,
  },
  fields: [
    {
      name: "locale",
      type: "text",
      admin: {
        readOnly: true,
      },
    },
    {
      name: "fallbackLocale",
      type: "json",
      admin: {
        readOnly: true,
      },
    },
    {
      name: "defaultLocale",
      type: "text",
      admin: {
        readOnly: true,
      },
    },
    {
      name: "availableLocales",
      type: "json",
      admin: {
        readOnly: true,
      },
    },
  ],
};

export const attachLocaleMetadata: CollectionAfterReadHook = ({ doc, req }) => ({
  ...doc,
  localeMeta: buildLocaleMetadata(req),
});

export const withLocaleSupport = <T extends CollectionConfig>(collection: T): T =>
  ({
    ...collection,
    fields: [...collection.fields, localeMetadataField],
    hooks: {
      ...collection.hooks,
      afterRead: [...(collection.hooks?.afterRead ?? []), attachLocaleMetadata],
    },
  }) as T;
