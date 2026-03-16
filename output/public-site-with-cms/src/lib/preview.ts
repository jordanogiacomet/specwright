import "server-only";

import config from "@payload-config";
import { headers } from "next/headers";
import { createPayloadRequest, getPayload } from "payload";

import {
  getCurrentUserFromRequest,
  type AuthenticatedUser,
} from "@/lib/auth";
import { PUBLISHED_STATUS } from "@/lib/content-status";
import {
  DEFAULT_LOCALE,
  isSupportedLocale,
  type SupportedLocaleCode,
} from "@/lib/i18n";
import { isEditorialUser } from "@/lib/permissions";
import type { Article } from "@/payload-types";

const ARTICLES_COLLECTION = "articles" as const;
const PREVIEW_ROUTE_BASE = "/preview";

type PreviewSearchParam = string | string[] | null | undefined;

export type ArticlePreviewResult =
  | {
      locale: SupportedLocaleCode;
      previewUrl: string;
      status: "forbidden";
      user: AuthenticatedUser;
    }
  | {
      locale: SupportedLocaleCode;
      previewUrl: string;
      status: "login-required";
    }
  | {
      locale: SupportedLocaleCode;
      previewUrl: string;
      status: "not-found";
      user: AuthenticatedUser;
    }
  | {
      article: Article;
      locale: SupportedLocaleCode;
      previewUrl: string;
      status: "ready";
      user: AuthenticatedUser;
    };

const getSearchParamValue = (value: PreviewSearchParam): string | null => {
  if (Array.isArray(value)) {
    return value[0] ?? null;
  }

  return value ?? null;
};

const getCurrentOrigin = (requestHeaders: Headers): string => {
  const forwardedHost = requestHeaders.get("x-forwarded-host");
  const host = forwardedHost ?? requestHeaders.get("host") ?? "localhost:3000";
  const protocol =
    requestHeaders.get("x-forwarded-proto") ??
    (host.startsWith("localhost") || host.startsWith("127.0.0.1")
      ? "http"
      : "https");

  return `${protocol}://${host}`;
};

const createPreviewRequest = async (pathname: string): Promise<Request> => {
  const currentHeaders = await headers();
  const requestHeaders = new Headers();

  for (const [key, value] of currentHeaders.entries()) {
    requestHeaders.set(key, value);
  }

  return new Request(new URL(pathname, getCurrentOrigin(requestHeaders)), {
    headers: requestHeaders,
    method: "GET",
  });
};

export const resolvePreviewLocale = (
  value: PreviewSearchParam,
): SupportedLocaleCode => {
  const locale = getSearchParamValue(value);

  return locale && isSupportedLocale(locale) ? locale : DEFAULT_LOCALE;
};

export const buildArticlePreviewUrl = ({
  locale = DEFAULT_LOCALE,
  slug,
}: {
  locale?: SupportedLocaleCode;
  slug: string;
}): string => {
  const pathname = `${PREVIEW_ROUTE_BASE}/${encodeURIComponent(slug)}`;

  if (locale === DEFAULT_LOCALE) {
    return pathname;
  }

  return `${pathname}?${new URLSearchParams({ locale }).toString()}`;
};

export const canAccessPreview = (
  user: AuthenticatedUser | null,
): user is AuthenticatedUser => isEditorialUser(user);

export async function getArticlePreview({
  locale: requestedLocale,
  slug,
}: {
  locale?: PreviewSearchParam;
  slug: string;
}): Promise<ArticlePreviewResult> {
  const locale = resolvePreviewLocale(requestedLocale);
  const previewUrl = buildArticlePreviewUrl({
    locale,
    slug,
  });
  const request = await createPreviewRequest(previewUrl);
  const user = await getCurrentUserFromRequest(request);

  if (!user) {
    return {
      locale,
      previewUrl,
      status: "login-required",
    };
  }

  if (!canAccessPreview(user)) {
    return {
      locale,
      previewUrl,
      status: "forbidden",
      user,
    };
  }

  const payload = await getPayload({
    config,
  });
  const payloadRequest = await createPayloadRequest({
    canSetHeaders: false,
    config,
    request,
  });
  const { docs } = await payload.find({
    collection: ARTICLES_COLLECTION,
    depth: 0,
    limit: 1,
    locale,
    overrideAccess: false,
    req: payloadRequest,
    where: {
      and: [
        {
          slug: {
            equals: slug,
          },
        },
        {
          status: {
            not_equals: PUBLISHED_STATUS,
          },
        },
      ],
    },
  });
  const article = docs[0] ?? null;

  if (!article) {
    return {
      locale,
      previewUrl,
      status: "not-found",
      user,
    };
  }

  return {
    article,
    locale,
    previewUrl,
    status: "ready",
    user,
  };
}
