import type {
  Field,
  LocalizationConfig,
  PayloadRequest,
  TypedFallbackLocale,
} from "payload";

export const supportedLocales = [
  {
    code: "en",
    label: "English",
  },
  {
    code: "pt",
    fallbackLocale: "en",
    label: "Portuguese",
  },
] as const;

export type AppLocale = (typeof supportedLocales)[number]["code"];

export const defaultLocale: AppLocale = "en";
export const localeCodes = supportedLocales.map(({ code }) => code) as AppLocale[];

const localeCodeSet = new Set<string>(localeCodes);

type LocaleRequest = Pick<PayloadRequest, "fallbackLocale" | "locale">;
type LocalizedTextObject = Partial<Record<AppLocale, null | string | undefined>>;

type LocalizedTextValidationOptions = {
  fieldLabel: string;
  maxLength?: number;
  minLength?: number;
  requiredInDefaultLocale?: boolean;
};

export type LocaleMetadata = {
  availableLocales: AppLocale[];
  defaultLocale: AppLocale;
  fallbackLocale: false | TypedFallbackLocale;
  locale: AppLocale | "all";
};

export const localizationConfig: LocalizationConfig = {
  defaultLocale,
  fallback: true,
  locales: [...supportedLocales],
};

function normalizePathname(pathname: string): string {
  const [pathOnly = "/"] = pathname.split(/[?#]/, 1);
  const trimmedPath = pathOnly.trim();

  if (trimmedPath.length === 0 || trimmedPath === "/") {
    return "/";
  }

  const withLeadingSlash = trimmedPath.startsWith("/")
    ? trimmedPath
    : `/${trimmedPath}`;
  const collapsedSlashes = withLeadingSlash.replace(/\/{2,}/g, "/");

  return collapsedSlashes.replace(/\/+$/g, "") || "/";
}

export function isAppLocale(value: string): value is AppLocale {
  return localeCodeSet.has(value);
}

export function resolveAppLocale(
  value: null | string | undefined,
): AppLocale {
  return typeof value === "string" && isAppLocale(value) ? value : defaultLocale;
}

export function getPathnameWithoutLocale(pathname: string): string {
  const segments = normalizePathname(pathname).split("/").filter(Boolean);

  if (segments.length > 0 && isAppLocale(segments[0] ?? "")) {
    segments.shift();
  }

  return segments.length > 0 ? `/${segments.join("/")}` : "/";
}

export function getLocalePathname(
  locale: AppLocale,
  pathname = "/",
): string {
  const pathnameWithoutLocale = getPathnameWithoutLocale(pathname);

  return pathnameWithoutLocale === "/"
    ? `/${locale}`
    : `/${locale}${pathnameWithoutLocale}`;
}

function isLocalizedTextObject(value: unknown): value is LocalizedTextObject {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function normalizeText(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function getTextForLocale(value: unknown, locale: AppLocale): string {
  if (typeof value === "string") {
    return normalizeText(value);
  }

  if (!isLocalizedTextObject(value)) {
    return "";
  }

  return normalizeText(value[locale]);
}

function getTextValuesForValidation(
  value: unknown,
  locale: AppLocale | "all",
): string[] {
  if (typeof value === "string") {
    const textValue = normalizeText(value);

    return textValue.length > 0 ? [textValue] : [];
  }

  if (!isLocalizedTextObject(value)) {
    return [];
  }

  if (locale === "all") {
    return localeCodes
      .map((localeCode) => normalizeText(value[localeCode]))
      .filter((textValue) => textValue.length > 0);
  }

  const textValue = normalizeText(value[locale]);

  return textValue.length > 0 ? [textValue] : [];
}

export function getActiveLocale(req: LocaleRequest): AppLocale | "all" {
  if (req.locale === "all") {
    return "all";
  }

  if (typeof req.locale === "string" && isAppLocale(req.locale)) {
    return req.locale;
  }

  return defaultLocale;
}

export function validateLocalizedText(
  value: unknown,
  req: LocaleRequest,
  {
    fieldLabel,
    maxLength,
    minLength,
    requiredInDefaultLocale = false,
  }: LocalizedTextValidationOptions,
): string | true {
  const activeLocale = getActiveLocale(req);
  const defaultLocaleValue = getTextForLocale(value, defaultLocale);
  const shouldRequireDefaultLocale =
    requiredInDefaultLocale &&
    (activeLocale === "all" || activeLocale === defaultLocale);

  if (shouldRequireDefaultLocale && defaultLocaleValue.length === 0) {
    return `${fieldLabel} is required in the default locale.`;
  }

  const valuesToValidate = getTextValuesForValidation(value, activeLocale);

  for (const textValue of valuesToValidate) {
    if (typeof minLength === "number" && textValue.length < minLength) {
      return `${fieldLabel} must be at least ${minLength} characters long.`;
    }

    if (typeof maxLength === "number" && textValue.length > maxLength) {
      return `${fieldLabel} must be ${maxLength} characters or fewer.`;
    }
  }

  return true;
}

export function getLocaleMetadata(req: LocaleRequest): LocaleMetadata {
  return {
    availableLocales: [...localeCodes],
    defaultLocale,
    fallbackLocale: req.fallbackLocale ?? false,
    locale: getActiveLocale(req),
  };
}

export function createLocaleMetaField(): Field {
  return {
    name: "localeMeta",
    type: "json",
    admin: {
      hidden: true,
      readOnly: true,
    },
    hooks: {
      afterRead: [
        ({ req }) => {
          return getLocaleMetadata(req);
        },
      ],
    },
    virtual: true,
  };
}
