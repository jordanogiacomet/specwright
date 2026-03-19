import { randomUUID } from "node:crypto";

import {
  defaultLocale,
  getAvailableLocales,
  getLocaleFallbackChain,
  isLocaleCode,
  localeConfig,
  resolveLocalizedText,
  supportedLocales,
  type AppLocale,
  type LocalizedTextPatch,
  type LocalizedTextValue,
} from "../lib/i18n";
import { query } from "../lib/db";

const ARTICLE_TITLE_MAX_LENGTH = 160;
const ARTICLE_EXCERPT_MAX_LENGTH = 320;
const ARTICLE_BODY_MAX_LENGTH = 20_000;
const MEDIA_FILE_NAME_MAX_LENGTH = 255;
const MEDIA_MIME_TYPE_MAX_LENGTH = 255;
const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const CONTENT_API_BASE_PATH = "/api/content";
const PUBLICATION_STATUS_VALUES = ["draft", "published"] as const;

type LocalizedArticleFieldName = "title" | "excerpt" | "body";
type CollectionFieldType =
  | "date"
  | "relationship"
  | "richText"
  | "text"
  | "upload";

type CollectionFieldDefinition = {
  name: string;
  type: CollectionFieldType;
  required: boolean;
  localized?: boolean;
  maxLength?: number;
  pattern?: string;
  relation?: string;
  allowedKinds?: MediaKind[];
};

type CollectionDefinition = {
  name: string;
  label: string;
  adminPath: string;
  localization?: typeof localeConfig;
  fields: CollectionFieldDefinition[];
};

type ArticleLocalizedFields = Record<
  LocalizedArticleFieldName,
  LocalizedTextValue
>;
type ArticleLocalizedFieldUpdates = Record<
  LocalizedArticleFieldName,
  LocalizedFieldUpdateInput | undefined
>;

type LocalizedFieldUpdateInput = {
  defaultValue?: string;
  translations?: LocalizedTextPatch;
};

type ArticleLocaleMetadata = {
  requested: AppLocale;
  default: AppLocale;
  fallbackChain: AppLocale[];
  available: AppLocale[];
  resolved: Record<LocalizedArticleFieldName, AppLocale>;
};

export type PublicationStatus = (typeof PUBLICATION_STATUS_VALUES)[number];

export type EditorialWorkflowDefinition = {
  mode: "crud-only" | "draft-publish";
  supportsDraftPublish: boolean;
  operations: Array<"create" | "delete" | "publish" | "read" | "update">;
  scheduleField?: "publishAt";
};

export type MediaKind = "image" | "file";

export type MediaAsset = {
  id: string;
  kind: MediaKind;
  originalName: string;
  fileName: string;
  mimeType: string;
  sizeBytes: number;
  createdAt: string;
  fileUrl: string;
};

export type ArticleRecord = {
  id: string;
  slug: string;
  defaultLocale: AppLocale;
  title: string;
  excerpt: string;
  body: string;
  publicationStatus: PublicationStatus;
  publishAt: string | null;
  publishedAt: string | null;
  translations: ArticleLocalizedFields;
  locale: ArticleLocaleMetadata;
  heroImage: MediaAsset | null;
  attachmentFile: MediaAsset | null;
  createdAt: string;
  updatedAt: string;
};

export type CreateArticleInput = {
  slug: string;
  defaultLocale: AppLocale;
  title: LocalizedTextValue;
  excerpt: LocalizedTextValue;
  body: LocalizedTextValue;
  publicationStatus: PublicationStatus;
  publishAt: string | null;
  heroImageId: string | null;
  attachmentFileId: string | null;
};

export type UpdateArticleInput = {
  slug?: string;
  defaultLocale?: AppLocale;
  title?: LocalizedFieldUpdateInput;
  excerpt?: LocalizedFieldUpdateInput;
  body?: LocalizedFieldUpdateInput;
  publicationStatus?: PublicationStatus;
  publishAt?: string | null;
  heroImageId?: string | null;
  attachmentFileId?: string | null;
};

export type ArticleVisibilityOptions = {
  includeDrafts?: boolean;
};

export type CreateMediaAssetInput = {
  kind: MediaKind;
  originalName: string;
  fileName: string;
  mimeType: string;
  sizeBytes: number;
  storagePath: string;
};

type MediaAssetRow = {
  id: string;
  kind: MediaKind;
  original_name: string;
  file_name: string;
  mime_type: string;
  size_bytes: number;
  storage_path: string;
  created_at: Date | string;
};

type ArticleRow = {
  id: string;
  slug: string;
  default_locale: string;
  title: string;
  title_translations: unknown;
  excerpt: string;
  excerpt_translations: unknown;
  body: string;
  body_translations: unknown;
  publication_status: PublicationStatus;
  publish_at: Date | string | null;
  published_at: Date | string | null;
  created_at: Date | string;
  updated_at: Date | string;
  hero_media_id: string | null;
  hero_media_kind: MediaKind | null;
  hero_media_original_name: string | null;
  hero_media_file_name: string | null;
  hero_media_mime_type: string | null;
  hero_media_size_bytes: number | null;
  hero_media_created_at: Date | string | null;
  hero_media_storage_path: string | null;
  attachment_media_id: string | null;
  attachment_media_kind: MediaKind | null;
  attachment_media_original_name: string | null;
  attachment_media_file_name: string | null;
  attachment_media_mime_type: string | null;
  attachment_media_size_bytes: number | null;
  attachment_media_created_at: Date | string | null;
  attachment_media_storage_path: string | null;
};

const localizedArticleFieldConfig = {
  title: ARTICLE_TITLE_MAX_LENGTH,
  excerpt: ARTICLE_EXCERPT_MAX_LENGTH,
  body: ARTICLE_BODY_MAX_LENGTH,
} as const;

export const mediaCollection: CollectionDefinition = {
  name: "media-assets",
  label: "Media Assets",
  adminPath: `${CONTENT_API_BASE_PATH}/media`,
  fields: [
    {
      name: "kind",
      type: "text",
      required: true,
    },
    {
      name: "originalName",
      type: "text",
      required: true,
      maxLength: MEDIA_FILE_NAME_MAX_LENGTH,
    },
    {
      name: "mimeType",
      type: "text",
      required: true,
      maxLength: MEDIA_MIME_TYPE_MAX_LENGTH,
    },
    {
      name: "file",
      type: "upload",
      required: true,
      allowedKinds: ["image", "file"],
    },
  ],
};

export const articleCollection: CollectionDefinition = {
  name: "articles",
  label: "Articles",
  adminPath: `${CONTENT_API_BASE_PATH}/articles`,
  localization: localeConfig,
  fields: [
    {
      name: "slug",
      type: "text",
      required: true,
      maxLength: 160,
      pattern: SLUG_PATTERN.source,
    },
    {
      name: "defaultLocale",
      type: "text",
      required: true,
      pattern: `^(${supportedLocales.join("|")})$`,
    },
    {
      name: "title",
      type: "text",
      required: true,
      localized: true,
      maxLength: ARTICLE_TITLE_MAX_LENGTH,
    },
    {
      name: "excerpt",
      type: "text",
      required: true,
      localized: true,
      maxLength: ARTICLE_EXCERPT_MAX_LENGTH,
    },
    {
      name: "body",
      type: "richText",
      required: true,
      localized: true,
      maxLength: ARTICLE_BODY_MAX_LENGTH,
    },
    {
      name: "publicationStatus",
      type: "text",
      required: true,
      pattern: `^(${PUBLICATION_STATUS_VALUES.join("|")})$`,
    },
    {
      name: "publishAt",
      type: "date",
      required: false,
    },
    {
      name: "heroImageId",
      type: "relationship",
      required: false,
      relation: "media-assets",
      allowedKinds: ["image"],
    },
    {
      name: "attachmentFileId",
      type: "relationship",
      required: false,
      relation: "media-assets",
      allowedKinds: ["file"],
    },
  ],
};

export const contentCollections = [articleCollection, mediaCollection];

export const editorialWorkflow: EditorialWorkflowDefinition = {
  mode: "draft-publish",
  supportsDraftPublish: true,
  operations: ["create", "read", "update", "delete", "publish"],
  scheduleField: "publishAt",
};

export class ContentValidationError extends Error {
  readonly details?: string[];

  constructor(message: string, details?: string[]) {
    super(message);
    this.name = "ContentValidationError";
    this.details = details;
  }
}

export class ContentNotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ContentNotFoundError";
  }
}

export class ContentConflictError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ContentConflictError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOwnProperty(object: Record<string, unknown>, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(object, key);
}

function normalizeRequiredText(
  value: unknown,
  fieldName: string,
  maxLength: number,
): string {
  if (typeof value !== "string") {
    throw new ContentValidationError(`${fieldName} must be a string.`);
  }

  const normalizedValue = value.trim();

  if (!normalizedValue) {
    throw new ContentValidationError(`${fieldName} is required.`);
  }

  if (normalizedValue.length > maxLength) {
    throw new ContentValidationError(
      `${fieldName} must be ${maxLength} characters or fewer.`,
    );
  }

  return normalizedValue;
}

function normalizeOptionalMediaId(
  value: unknown,
  fieldName: string,
): string | null {
  if (value === undefined || value === null) {
    return null;
  }

  if (typeof value !== "string") {
    throw new ContentValidationError(`${fieldName} must be a string or null.`);
  }

  const normalizedValue = value.trim();

  if (!normalizedValue) {
    return null;
  }

  return normalizedValue;
}

function normalizeSlug(value: unknown): string {
  const slug = normalizeRequiredText(value, "slug", 160).toLowerCase();

  if (!SLUG_PATTERN.test(slug)) {
    throw new ContentValidationError(
      "slug must use lowercase letters, numbers, and hyphens only.",
    );
  }

  return slug;
}

function normalizeLocale(value: unknown, fieldName: string): AppLocale {
  if (!isLocaleCode(value)) {
    throw new ContentValidationError(
      `${fieldName} must be one of: ${supportedLocales.join(", ")}.`,
    );
  }

  return value;
}

function normalizePublicationStatus(
  value: unknown,
  fieldName: string,
): PublicationStatus {
  if (
    typeof value !== "string" ||
    !PUBLICATION_STATUS_VALUES.includes(value as PublicationStatus)
  ) {
    throw new ContentValidationError(
      `${fieldName} must be one of: ${PUBLICATION_STATUS_VALUES.join(", ")}.`,
    );
  }

  return value as PublicationStatus;
}

function normalizeOptionalDateTime(
  value: unknown,
  fieldName: string,
): string | null {
  if (value === undefined || value === null) {
    return null;
  }

  if (typeof value !== "string") {
    throw new ContentValidationError(`${fieldName} must be a string or null.`);
  }

  const normalizedValue = value.trim();

  if (!normalizedValue) {
    return null;
  }

  const parsedValue = new Date(normalizedValue);

  if (Number.isNaN(parsedValue.getTime())) {
    throw new ContentValidationError(
      `${fieldName} must be a valid ISO-8601 datetime string.`,
    );
  }

  return parsedValue.toISOString();
}

function normalizeLocalizedFieldEntries(
  value: unknown,
  fieldName: LocalizedArticleFieldName,
  maxLength: number,
  allowNullValues: boolean,
): LocalizedTextValue | LocalizedTextPatch {
  if (!isRecord(value)) {
    throw new ContentValidationError(
      `${fieldName} must be a string or an object keyed by locale.`,
    );
  }

  const normalizedEntries: LocalizedTextValue | LocalizedTextPatch = {};

  for (const [locale, localeValue] of Object.entries(value)) {
    if (!isLocaleCode(locale)) {
      throw new ContentValidationError(
        `${fieldName} contains an unsupported locale: ${locale}.`,
      );
    }

    if (localeValue === null) {
      if (!allowNullValues) {
        throw new ContentValidationError(`${fieldName}.${locale} is required.`);
      }

      normalizedEntries[locale] = null;
      continue;
    }

    normalizedEntries[locale] = normalizeRequiredText(
      localeValue,
      `${fieldName}.${locale}`,
      maxLength,
    );
  }

  if (Object.keys(normalizedEntries).length === 0) {
    throw new ContentValidationError(
      `${fieldName} must include at least one locale value.`,
    );
  }

  return normalizedEntries;
}

function normalizeCreateLocalizedFieldInput(
  value: unknown,
  fieldName: LocalizedArticleFieldName,
  defaultLocaleCode: AppLocale,
): LocalizedTextValue {
  if (typeof value === "string") {
    return {
      [defaultLocaleCode]: normalizeRequiredText(
        value,
        fieldName,
        localizedArticleFieldConfig[fieldName],
      ),
    };
  }

  const normalizedEntries = normalizeLocalizedFieldEntries(
    value,
    fieldName,
    localizedArticleFieldConfig[fieldName],
    false,
  ) as LocalizedTextValue;

  if (!normalizedEntries[defaultLocaleCode]) {
    throw new ContentValidationError(
      `${fieldName}.${defaultLocaleCode} is required for the default locale.`,
    );
  }

  return normalizedEntries;
}

function normalizeUpdateLocalizedFieldInput(
  value: unknown,
  fieldName: LocalizedArticleFieldName,
): LocalizedFieldUpdateInput {
  if (typeof value === "string") {
    return {
      defaultValue: normalizeRequiredText(
        value,
        fieldName,
        localizedArticleFieldConfig[fieldName],
      ),
    };
  }

  return {
    translations: normalizeLocalizedFieldEntries(
      value,
      fieldName,
      localizedArticleFieldConfig[fieldName],
      true,
    ) as LocalizedTextPatch,
  };
}

function normalizeCreateArticleInput(payload: unknown): CreateArticleInput {
  if (!isRecord(payload)) {
    throw new ContentValidationError("Article payload must be a JSON object.");
  }

  const normalizedDefaultLocale = hasOwnProperty(payload, "defaultLocale")
    ? normalizeLocale(payload.defaultLocale, "defaultLocale")
    : defaultLocale;
  const normalizedPublishAt = hasOwnProperty(payload, "publishAt")
    ? normalizeOptionalDateTime(payload.publishAt, "publishAt")
    : null;
  const normalizedPublicationStatus = hasOwnProperty(payload, "publicationStatus")
    ? normalizePublicationStatus(payload.publicationStatus, "publicationStatus")
    : normalizedPublishAt
      ? "draft"
      : "published";

  return {
    slug: normalizeSlug(payload.slug),
    defaultLocale: normalizedDefaultLocale,
    title: normalizeCreateLocalizedFieldInput(
      payload.title,
      "title",
      normalizedDefaultLocale,
    ),
    excerpt: normalizeCreateLocalizedFieldInput(
      payload.excerpt,
      "excerpt",
      normalizedDefaultLocale,
    ),
    body: normalizeCreateLocalizedFieldInput(
      payload.body,
      "body",
      normalizedDefaultLocale,
    ),
    publicationStatus: normalizedPublicationStatus,
    publishAt: normalizedPublishAt,
    heroImageId: normalizeOptionalMediaId(payload.heroImageId, "heroImageId"),
    attachmentFileId: normalizeOptionalMediaId(
      payload.attachmentFileId,
      "attachmentFileId",
    ),
  };
}

function normalizeUpdateArticleInput(payload: unknown): UpdateArticleInput {
  if (!isRecord(payload)) {
    throw new ContentValidationError("Article payload must be a JSON object.");
  }

  const normalizedPayload: UpdateArticleInput = {};

  if (hasOwnProperty(payload, "slug")) {
    normalizedPayload.slug = normalizeSlug(payload.slug);
  }

  if (hasOwnProperty(payload, "defaultLocale")) {
    normalizedPayload.defaultLocale = normalizeLocale(
      payload.defaultLocale,
      "defaultLocale",
    );
  }

  if (hasOwnProperty(payload, "title")) {
    normalizedPayload.title = normalizeUpdateLocalizedFieldInput(
      payload.title,
      "title",
    );
  }

  if (hasOwnProperty(payload, "excerpt")) {
    normalizedPayload.excerpt = normalizeUpdateLocalizedFieldInput(
      payload.excerpt,
      "excerpt",
    );
  }

  if (hasOwnProperty(payload, "body")) {
    normalizedPayload.body = normalizeUpdateLocalizedFieldInput(
      payload.body,
      "body",
    );
  }

  if (hasOwnProperty(payload, "publicationStatus")) {
    normalizedPayload.publicationStatus = normalizePublicationStatus(
      payload.publicationStatus,
      "publicationStatus",
    );
  }

  if (hasOwnProperty(payload, "publishAt")) {
    normalizedPayload.publishAt = normalizeOptionalDateTime(
      payload.publishAt,
      "publishAt",
    );
  }

  if (hasOwnProperty(payload, "heroImageId")) {
    normalizedPayload.heroImageId = normalizeOptionalMediaId(
      payload.heroImageId,
      "heroImageId",
    );
  }

  if (hasOwnProperty(payload, "attachmentFileId")) {
    normalizedPayload.attachmentFileId = normalizeOptionalMediaId(
      payload.attachmentFileId,
      "attachmentFileId",
    );
  }

  if (Object.keys(normalizedPayload).length === 0) {
    throw new ContentValidationError(
      "At least one article field must be provided.",
    );
  }

  return normalizedPayload;
}

function normalizeCreateMediaAssetInput(
  payload: CreateMediaAssetInput,
): CreateMediaAssetInput {
  const originalName = normalizeRequiredText(
    payload.originalName,
    "originalName",
    MEDIA_FILE_NAME_MAX_LENGTH,
  );
  const fileName = normalizeRequiredText(
    payload.fileName,
    "fileName",
    MEDIA_FILE_NAME_MAX_LENGTH,
  );
  const mimeType = normalizeRequiredText(
    payload.mimeType,
    "mimeType",
    MEDIA_MIME_TYPE_MAX_LENGTH,
  ).toLowerCase();
  const storagePath = normalizeRequiredText(
    payload.storagePath,
    "storagePath",
    1_000,
  );

  if (payload.kind !== "image" && payload.kind !== "file") {
    throw new ContentValidationError("kind must be either image or file.");
  }

  if (!Number.isInteger(payload.sizeBytes) || payload.sizeBytes < 1) {
    throw new ContentValidationError("sizeBytes must be a positive integer.");
  }

  return {
    kind: payload.kind,
    originalName,
    fileName,
    mimeType,
    sizeBytes: payload.sizeBytes,
    storagePath,
  };
}

function normalizeStoredLocalizedText(
  value: unknown,
  fieldName: LocalizedArticleFieldName,
): LocalizedTextValue {
  if (value === null || value === undefined) {
    return {};
  }

  if (!isRecord(value)) {
    throw new Error(`${fieldName}_translations must be an object.`);
  }

  const normalizedEntries: LocalizedTextValue = {};

  for (const [locale, localeValue] of Object.entries(value)) {
    if (!isLocaleCode(locale)) {
      continue;
    }

    if (typeof localeValue !== "string") {
      throw new Error(`${fieldName}.${locale} must be a string in storage.`);
    }

    normalizedEntries[locale] = normalizeRequiredText(
      localeValue,
      `${fieldName}.${locale}`,
      localizedArticleFieldConfig[fieldName],
    );
  }

  return normalizedEntries;
}

function mergeStoredLocalizedField(
  rowValue: string,
  rowTranslations: unknown,
  fieldName: LocalizedArticleFieldName,
  defaultLocaleCode: AppLocale,
): LocalizedTextValue {
  return {
    ...normalizeStoredLocalizedText(rowTranslations, fieldName),
    [defaultLocaleCode]: normalizeRequiredText(
      rowValue,
      `${fieldName}.${defaultLocaleCode}`,
      localizedArticleFieldConfig[fieldName],
    ),
  };
}

function getArticleLocalizedFields(row: ArticleRow): ArticleLocalizedFields {
  const articleDefaultLocale = normalizeLocale(
    row.default_locale,
    "defaultLocale",
  );

  return {
    title: mergeStoredLocalizedField(
      row.title,
      row.title_translations,
      "title",
      articleDefaultLocale,
    ),
    excerpt: mergeStoredLocalizedField(
      row.excerpt,
      row.excerpt_translations,
      "excerpt",
      articleDefaultLocale,
    ),
    body: mergeStoredLocalizedField(
      row.body,
      row.body_translations,
      "body",
      articleDefaultLocale,
    ),
  };
}

function applyLocalizedFieldUpdate(
  currentValue: LocalizedTextValue,
  update: LocalizedFieldUpdateInput | undefined,
  fieldName: LocalizedArticleFieldName,
  nextDefaultLocale: AppLocale,
): LocalizedTextValue {
  const nextValue: LocalizedTextValue = { ...currentValue };

  if (update?.translations) {
    for (const locale of supportedLocales) {
      const localeValue = update.translations[locale];

      if (localeValue === undefined) {
        continue;
      }

      if (localeValue === null) {
        delete nextValue[locale];
        continue;
      }

      nextValue[locale] = localeValue;
    }
  }

  if (update?.defaultValue !== undefined) {
    const existingTranslatedValue = update.translations?.[nextDefaultLocale];

    if (
      typeof existingTranslatedValue === "string" &&
      existingTranslatedValue !== update.defaultValue
    ) {
      throw new ContentValidationError(
        `${fieldName}.${nextDefaultLocale} must match ${fieldName} when both are provided.`,
      );
    }

    if (existingTranslatedValue === null) {
      throw new ContentValidationError(
        `${fieldName}.${nextDefaultLocale} cannot be cleared while it is the default locale.`,
      );
    }

    nextValue[nextDefaultLocale] = update.defaultValue;
  }

  const defaultLocaleValue = nextValue[nextDefaultLocale];

  if (!defaultLocaleValue) {
    throw new ContentValidationError(
      `${fieldName}.${nextDefaultLocale} is required for the default locale.`,
    );
  }

  return nextValue;
}

function splitLocalizedFieldForStorage(
  localizedValue: LocalizedTextValue,
  fieldName: LocalizedArticleFieldName,
  defaultLocaleCode: AppLocale,
): { defaultValue: string; translations: LocalizedTextValue } {
  const defaultValue = localizedValue[defaultLocaleCode];

  if (!defaultValue) {
    throw new ContentValidationError(
      `${fieldName}.${defaultLocaleCode} is required for the default locale.`,
    );
  }

  const translations: LocalizedTextValue = {};

  for (const locale of supportedLocales) {
    if (locale === defaultLocaleCode) {
      continue;
    }

    const value = localizedValue[locale];

    if (typeof value === "string" && value.trim()) {
      translations[locale] = value;
    }
  }

  return {
    defaultValue,
    translations,
  };
}

function toIsoString(value: Date | string): string {
  if (value instanceof Date) {
    return value.toISOString();
  }

  return new Date(value).toISOString();
}

function toOptionalIsoString(value: Date | string | null): string | null {
  if (!value) {
    return null;
  }

  return toIsoString(value);
}

function buildMediaFileUrl(mediaId: string): string {
  return `${CONTENT_API_BASE_PATH}/media/${mediaId}/file`;
}

function mapMediaAssetRow(row: MediaAssetRow): MediaAsset {
  return {
    id: row.id,
    kind: row.kind,
    originalName: row.original_name,
    fileName: row.file_name,
    mimeType: row.mime_type,
    sizeBytes: row.size_bytes,
    createdAt: toIsoString(row.created_at),
    fileUrl: buildMediaFileUrl(row.id),
  };
}

function mapArticleMedia(
  prefix: "hero" | "attachment",
  row: ArticleRow,
): MediaAsset | null {
  const columnPrefix = prefix === "hero" ? "hero_media" : "attachment_media";
  const id = row[`${columnPrefix}_id`];

  if (!id) {
    return null;
  }

  return {
    id,
    kind: row[`${columnPrefix}_kind`] as MediaKind,
    originalName: row[`${columnPrefix}_original_name`] as string,
    fileName: row[`${columnPrefix}_file_name`] as string,
    mimeType: row[`${columnPrefix}_mime_type`] as string,
    sizeBytes: row[`${columnPrefix}_size_bytes`] as number,
    createdAt: toIsoString(row[`${columnPrefix}_created_at`] as Date | string),
    fileUrl: buildMediaFileUrl(id),
  };
}

function mapArticleRow(
  row: ArticleRow,
  requestedLocale: AppLocale,
): ArticleRecord {
  const articleDefaultLocale = normalizeLocale(
    row.default_locale,
    "defaultLocale",
  );
  const articleTranslations = getArticleLocalizedFields(row);
  const resolvedTitle = resolveLocalizedText(
    articleTranslations.title,
    requestedLocale,
    articleDefaultLocale,
  );
  const resolvedExcerpt = resolveLocalizedText(
    articleTranslations.excerpt,
    requestedLocale,
    articleDefaultLocale,
  );
  const resolvedBody = resolveLocalizedText(
    articleTranslations.body,
    requestedLocale,
    articleDefaultLocale,
  );

  if (!resolvedTitle || !resolvedExcerpt || !resolvedBody) {
    throw new Error(
      "Article translations are missing a required default locale value.",
    );
  }

  return {
    id: row.id,
    slug: row.slug,
    defaultLocale: articleDefaultLocale,
    title: resolvedTitle.value,
    excerpt: resolvedExcerpt.value,
    body: resolvedBody.value,
    publicationStatus: row.publication_status,
    publishAt: toOptionalIsoString(row.publish_at),
    publishedAt: toOptionalIsoString(row.published_at),
    translations: articleTranslations,
    locale: {
      requested: requestedLocale,
      default: articleDefaultLocale,
      fallbackChain: getLocaleFallbackChain(
        requestedLocale,
        articleDefaultLocale,
      ),
      available: getAvailableLocales(
        articleTranslations.title,
        articleTranslations.excerpt,
        articleTranslations.body,
      ),
      resolved: {
        title: resolvedTitle.locale,
        excerpt: resolvedExcerpt.locale,
        body: resolvedBody.locale,
      },
    },
    heroImage: mapArticleMedia("hero", row),
    attachmentFile: mapArticleMedia("attachment", row),
    createdAt: toIsoString(row.created_at),
    updatedAt: toIsoString(row.updated_at),
  };
}

function getArticleSelectQuery(): string {
  return `
    SELECT
      article.id,
      article.slug,
      article.default_locale,
      article.title,
      article.title_translations,
      article.excerpt,
      article.excerpt_translations,
      article.body,
      article.body_translations,
      article.publication_status,
      article.publish_at,
      article.published_at,
      article.created_at,
      article.updated_at,
      hero.id AS hero_media_id,
      hero.kind AS hero_media_kind,
      hero.original_name AS hero_media_original_name,
      hero.file_name AS hero_media_file_name,
      hero.mime_type AS hero_media_mime_type,
      hero.size_bytes AS hero_media_size_bytes,
      hero.created_at AS hero_media_created_at,
      hero.storage_path AS hero_media_storage_path,
      attachment.id AS attachment_media_id,
      attachment.kind AS attachment_media_kind,
      attachment.original_name AS attachment_media_original_name,
      attachment.file_name AS attachment_media_file_name,
      attachment.mime_type AS attachment_media_mime_type,
      attachment.size_bytes AS attachment_media_size_bytes,
      attachment.created_at AS attachment_media_created_at,
      attachment.storage_path AS attachment_media_storage_path
    FROM articles article
    LEFT JOIN media_assets hero ON hero.id = article.hero_image_id
    LEFT JOIN media_assets attachment ON attachment.id = article.attachment_file_id
  `;
}

async function getArticleRowById(
  id: string,
  options: ArticleVisibilityOptions = {},
): Promise<ArticleRow | null> {
  const { includeDrafts = true } = options;
  const result = await query<ArticleRow>(
    `${getArticleSelectQuery()} WHERE article.id = $1${
      includeDrafts ? "" : " AND article.publication_status = 'published'"
    }`,
    [id],
  );

  return result.rows[0] ?? null;
}

async function ensureMediaRelationship(
  mediaId: string | null,
  expectedKind: MediaKind,
  fieldName: string,
): Promise<void> {
  if (!mediaId) {
    return;
  }

  const result = await query<{ kind: MediaKind }>(
    "SELECT kind FROM media_assets WHERE id = $1",
    [mediaId],
  );

  if (!result.rows[0]) {
    throw new ContentValidationError(
      `${fieldName} references a missing media asset.`,
    );
  }

  if (result.rows[0].kind !== expectedKind) {
    throw new ContentValidationError(
      `${fieldName} must reference a ${expectedKind} media asset.`,
    );
  }
}

function translateDatabaseError(error: unknown): never {
  if (isRecord(error) && error.code === "23505") {
    throw new ContentConflictError(
      "A record with the same unique value already exists.",
    );
  }

  throw error;
}

export async function listArticles(
  requestedLocale: AppLocale = defaultLocale,
  options: ArticleVisibilityOptions = {},
): Promise<ArticleRecord[]> {
  const { includeDrafts = true } = options;
  const result = await query<ArticleRow>(
    `${getArticleSelectQuery()}${
      includeDrafts ? "" : " WHERE article.publication_status = 'published'"
    } ORDER BY article.created_at DESC`,
  );

  return result.rows.map((row) => mapArticleRow(row, requestedLocale));
}

export async function getArticleById(
  id: string,
  requestedLocale: AppLocale = defaultLocale,
  options: ArticleVisibilityOptions = {},
): Promise<ArticleRecord | null> {
  const row = await getArticleRowById(id, options);

  return row ? mapArticleRow(row, requestedLocale) : null;
}

export async function createArticle(
  payload: unknown,
  requestedLocale: AppLocale = defaultLocale,
): Promise<ArticleRecord> {
  const input = normalizeCreateArticleInput(payload);

  await ensureMediaRelationship(input.heroImageId, "image", "heroImageId");
  await ensureMediaRelationship(
    input.attachmentFileId,
    "file",
    "attachmentFileId",
  );

  const articleId = randomUUID();
  const titleStorage = splitLocalizedFieldForStorage(
    input.title,
    "title",
    input.defaultLocale,
  );
  const excerptStorage = splitLocalizedFieldForStorage(
    input.excerpt,
    "excerpt",
    input.defaultLocale,
  );
  const bodyStorage = splitLocalizedFieldForStorage(
    input.body,
    "body",
    input.defaultLocale,
  );
  const publishedAt =
    input.publicationStatus === "published" ? new Date().toISOString() : null;

  try {
    await query(
      `
        INSERT INTO articles (
          id,
          slug,
          default_locale,
          title,
          title_translations,
          excerpt,
          excerpt_translations,
          body,
          body_translations,
          publication_status,
          publish_at,
          published_at,
          hero_image_id,
          attachment_file_id
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
      `,
      [
        articleId,
        input.slug,
        input.defaultLocale,
        titleStorage.defaultValue,
        titleStorage.translations,
        excerptStorage.defaultValue,
        excerptStorage.translations,
        bodyStorage.defaultValue,
        bodyStorage.translations,
        input.publicationStatus,
        input.publishAt,
        publishedAt,
        input.heroImageId,
        input.attachmentFileId,
      ],
    );
  } catch (error) {
    translateDatabaseError(error);
  }

  const article = await getArticleById(articleId, requestedLocale);

  if (!article) {
    throw new ContentNotFoundError(
      "Article was created but could not be loaded.",
    );
  }

  return article;
}

export async function updateArticle(
  id: string,
  payload: unknown,
  requestedLocale: AppLocale = defaultLocale,
): Promise<ArticleRecord> {
  const input = normalizeUpdateArticleInput(payload);

  if (input.heroImageId !== undefined) {
    await ensureMediaRelationship(
      input.heroImageId ?? null,
      "image",
      "heroImageId",
    );
  }

  if (input.attachmentFileId !== undefined) {
    await ensureMediaRelationship(
      input.attachmentFileId ?? null,
      "file",
      "attachmentFileId",
    );
  }

  const existingArticle = await getArticleRowById(id);

  if (!existingArticle) {
    throw new ContentNotFoundError("Article not found.");
  }

  const currentDefaultLocale = normalizeLocale(
    existingArticle.default_locale,
    "defaultLocale",
  );
  const currentPublicationStatus = normalizePublicationStatus(
    existingArticle.publication_status,
    "publicationStatus",
  );
  const nextDefaultLocale = input.defaultLocale ?? currentDefaultLocale;
  const nextPublicationStatus =
    input.publicationStatus ?? currentPublicationStatus;
  const nextPublishAt =
    input.publishAt !== undefined
      ? input.publishAt
      : toOptionalIsoString(existingArticle.publish_at);
  const currentTranslations = getArticleLocalizedFields(existingArticle);
  const localizedFieldUpdates: ArticleLocalizedFieldUpdates = {
    title: input.title,
    excerpt: input.excerpt,
    body: input.body,
  };
  const shouldUpdateLocalizedFields =
    input.defaultLocale !== undefined ||
    input.title !== undefined ||
    input.excerpt !== undefined ||
    input.body !== undefined;

  if (
    currentPublicationStatus === "published" &&
    nextPublicationStatus === "draft"
  ) {
    throw new ContentValidationError(
      "Unpublishing an article is not supported.",
    );
  }

  const updates: string[] = [];
  const values: unknown[] = [];

  if (input.slug !== undefined) {
    updates.push(`slug = $${values.length + 1}`);
    values.push(input.slug);
  }

  if (shouldUpdateLocalizedFields) {
    const nextTranslations: ArticleLocalizedFields = {
      title: applyLocalizedFieldUpdate(
        currentTranslations.title,
        localizedFieldUpdates.title,
        "title",
        nextDefaultLocale,
      ),
      excerpt: applyLocalizedFieldUpdate(
        currentTranslations.excerpt,
        localizedFieldUpdates.excerpt,
        "excerpt",
        nextDefaultLocale,
      ),
      body: applyLocalizedFieldUpdate(
        currentTranslations.body,
        localizedFieldUpdates.body,
        "body",
        nextDefaultLocale,
      ),
    };
    const titleStorage = splitLocalizedFieldForStorage(
      nextTranslations.title,
      "title",
      nextDefaultLocale,
    );
    const excerptStorage = splitLocalizedFieldForStorage(
      nextTranslations.excerpt,
      "excerpt",
      nextDefaultLocale,
    );
    const bodyStorage = splitLocalizedFieldForStorage(
      nextTranslations.body,
      "body",
      nextDefaultLocale,
    );

    updates.push(`default_locale = $${values.length + 1}`);
    values.push(nextDefaultLocale);
    updates.push(`title = $${values.length + 1}`);
    values.push(titleStorage.defaultValue);
    updates.push(`title_translations = $${values.length + 1}`);
    values.push(titleStorage.translations);
    updates.push(`excerpt = $${values.length + 1}`);
    values.push(excerptStorage.defaultValue);
    updates.push(`excerpt_translations = $${values.length + 1}`);
    values.push(excerptStorage.translations);
    updates.push(`body = $${values.length + 1}`);
    values.push(bodyStorage.defaultValue);
    updates.push(`body_translations = $${values.length + 1}`);
    values.push(bodyStorage.translations);
  }

  if (input.heroImageId !== undefined) {
    updates.push(`hero_image_id = $${values.length + 1}`);
    values.push(input.heroImageId ?? null);
  }

  if (input.attachmentFileId !== undefined) {
    updates.push(`attachment_file_id = $${values.length + 1}`);
    values.push(input.attachmentFileId ?? null);
  }

  if (input.publicationStatus !== undefined || input.publishAt !== undefined) {
    const nextPublishedAt =
      nextPublicationStatus === "published"
        ? toOptionalIsoString(existingArticle.published_at) ??
          new Date().toISOString()
        : null;

    updates.push(`publication_status = $${values.length + 1}`);
    values.push(nextPublicationStatus);
    updates.push(`publish_at = $${values.length + 1}`);
    values.push(nextPublishAt);
    updates.push(`published_at = $${values.length + 1}`);
    values.push(nextPublishedAt);
  }

  updates.push("updated_at = CURRENT_TIMESTAMP");
  values.push(id);

  try {
    await query(
      `
        UPDATE articles
        SET ${updates.join(", ")}
        WHERE id = $${values.length}
      `,
      values,
    );
  } catch (error) {
    translateDatabaseError(error);
  }

  const article = await getArticleById(id, requestedLocale);

  if (!article) {
    throw new ContentNotFoundError("Article not found.");
  }

  return article;
}

export async function deleteArticle(id: string): Promise<void> {
  const result = await query("DELETE FROM articles WHERE id = $1", [id]);

  if ((result.rowCount ?? 0) === 0) {
    throw new ContentNotFoundError("Article not found.");
  }
}

export async function listMediaAssets(): Promise<MediaAsset[]> {
  const result = await query<MediaAssetRow>(
    "SELECT * FROM media_assets ORDER BY created_at DESC",
  );

  return result.rows.map(mapMediaAssetRow);
}

export async function getMediaAssetById(
  id: string,
): Promise<(MediaAsset & { storagePath: string }) | null> {
  const result = await query<MediaAssetRow>(
    "SELECT * FROM media_assets WHERE id = $1",
    [id],
  );
  const row = result.rows[0];

  if (!row) {
    return null;
  }

  return {
    ...mapMediaAssetRow(row),
    storagePath: row.storage_path,
  };
}

export async function createMediaAsset(
  payload: CreateMediaAssetInput,
): Promise<MediaAsset> {
  const input = normalizeCreateMediaAssetInput(payload);
  const mediaId = randomUUID();

  try {
    await query(
      `
        INSERT INTO media_assets (
          id,
          kind,
          original_name,
          file_name,
          mime_type,
          size_bytes,
          storage_path
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
      `,
      [
        mediaId,
        input.kind,
        input.originalName,
        input.fileName,
        input.mimeType,
        input.sizeBytes,
        input.storagePath,
      ],
    );
  } catch (error) {
    translateDatabaseError(error);
  }

  const media = await getMediaAssetById(mediaId);

  if (!media) {
    throw new ContentNotFoundError(
      "Media asset was created but could not be loaded.",
    );
  }

  return media;
}

export async function deleteMediaAsset(
  id: string,
): Promise<(MediaAsset & { storagePath: string }) | null> {
  const media = await getMediaAssetById(id);

  if (!media) {
    return null;
  }

  const usageResult = await query<{ article_count: string }>(
    `
      SELECT COUNT(*)::text AS article_count
      FROM articles
      WHERE hero_image_id = $1 OR attachment_file_id = $1
    `,
    [id],
  );

  if (Number.parseInt(usageResult.rows[0]?.article_count ?? "0", 10) > 0) {
    throw new ContentValidationError(
      "Media asset cannot be deleted while it is referenced by an article.",
    );
  }

  await query("DELETE FROM media_assets WHERE id = $1", [id]);

  return media;
}
