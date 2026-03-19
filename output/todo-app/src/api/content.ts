import { randomUUID } from "node:crypto";
import { access, mkdir, unlink, writeFile } from "node:fs/promises";
import path from "node:path";

import express, {
  Router,
  type ErrorRequestHandler,
  type Request,
  type RequestHandler,
  type Response,
} from "express";

import {
  defaultLocale,
  isLocaleCode,
  localeConfig,
  supportedLocales,
  type AppLocale,
} from "../lib/i18n";
import {
  articleCollection,
  contentCollections,
  createArticle,
  createMediaAsset,
  deleteArticle,
  deleteMediaAsset,
  editorialWorkflow,
  getArticleById,
  getMediaAssetById,
  listArticles,
  listMediaAssets,
  mediaCollection,
  type MediaKind,
  ContentConflictError,
  ContentNotFoundError,
  ContentValidationError,
  updateArticle,
} from "../models/Article";
import { createLogger } from "../lib/logger";

const DEFAULT_UPLOAD_DIRECTORY = "storage/uploads";
const DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

const contentLogger = createLogger({
  component: "content-router",
  service: "todo-app-api",
});

function getUploadDirectory(): string {
  return process.env.CMS_UPLOAD_DIR?.trim() || DEFAULT_UPLOAD_DIRECTORY;
}

function getUploadMaxBytes(): number {
  const configuredValue = process.env.CMS_UPLOAD_MAX_BYTES?.trim();

  if (!configuredValue) {
    return DEFAULT_MAX_UPLOAD_BYTES;
  }

  const parsedValue = Number.parseInt(configuredValue, 10);

  if (!Number.isInteger(parsedValue) || parsedValue < 1) {
    throw new Error("CMS_UPLOAD_MAX_BYTES must be a positive integer.");
  }

  return parsedValue;
}

function sanitizeFilename(filename: string): string {
  const trimmedValue = filename.trim() || "upload.bin";
  const extension = path
    .extname(trimmedValue)
    .toLowerCase()
    .replace(/[^.a-z0-9]/g, "");
  const basename = path
    .basename(trimmedValue, path.extname(trimmedValue))
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");

  return `${basename || "upload"}${extension}`;
}

function getUploadKind(request: Request): MediaKind {
  const kind = request.query.kind;

  if (kind !== "image" && kind !== "file") {
    throw new ContentValidationError(
      "Upload kind must be provided as ?kind=image or ?kind=file.",
    );
  }

  return kind;
}

function getUploadFilename(request: Request): string {
  const headerValue = request.header("x-upload-filename");

  if (!headerValue) {
    throw new ContentValidationError("x-upload-filename header is required.");
  }

  return sanitizeFilename(headerValue);
}

function getUploadMimeType(request: Request): string {
  const contentType = request
    .header("content-type")
    ?.split(";")[0]
    ?.trim()
    .toLowerCase();

  if (!contentType) {
    return "application/octet-stream";
  }

  return contentType;
}

function validateUploadMimeType(kind: MediaKind, mimeType: string): void {
  if (kind === "image" && !mimeType.startsWith("image/")) {
    throw new ContentValidationError(
      "Image uploads must use an image/* content type.",
    );
  }

  if (kind === "file" && mimeType.startsWith("image/")) {
    throw new ContentValidationError(
      "File uploads must not use an image/* content type.",
    );
  }
}

function getStorageSubdirectory(kind: MediaKind): string {
  return kind === "image" ? "images" : "files";
}

function buildRelativeStoragePath(kind: MediaKind, filename: string): string {
  const normalizedUploadDirectory = getUploadDirectory()
    .replace(/\\/g, "/")
    .replace(/\/$/, "");

  return `${normalizedUploadDirectory}/${getStorageSubdirectory(kind)}/${randomUUID()}-${filename}`;
}

function resolveStoragePath(relativeStoragePath: string): string {
  return path.resolve(process.cwd(), relativeStoragePath);
}

function asyncHandler(
  handler: (request: Request, response: Response) => Promise<void>,
): RequestHandler {
  return (request, response, next) => {
    void handler(request, response).catch(next);
  };
}

function getRequestedLocale(request: Request): AppLocale {
  const locale = Array.isArray(request.query.locale)
    ? request.query.locale[0]
    : request.query.locale;

  if (locale === undefined) {
    return defaultLocale;
  }

  if (typeof locale !== "string" || !isLocaleCode(locale)) {
    throw new ContentValidationError(
      `locale must be one of: ${supportedLocales.join(", ")}.`,
    );
  }

  return locale;
}

function getIncludeDrafts(request: Request): boolean {
  const includeDrafts = Array.isArray(request.query.includeDrafts)
    ? request.query.includeDrafts[0]
    : request.query.includeDrafts;

  if (includeDrafts === undefined) {
    return false;
  }

  if (includeDrafts === "true") {
    return true;
  }

  if (includeDrafts === "false") {
    return false;
  }

  throw new ContentValidationError("includeDrafts must be true or false.");
}

const schemaHandler: RequestHandler = (_request, response) => {
  response.json({
    i18n: localeConfig,
    collections: contentCollections,
    workflow: editorialWorkflow,
    media: {
      collection: mediaCollection,
      uploadEndpoint: "/api/content/media",
      maxUploadBytes: getUploadMaxBytes(),
      supportedKinds: ["image", "file"],
    },
    admin: {
      basePath: "/api/content",
      i18n: localeConfig,
      articleCollection,
    },
  });
};

const listArticlesHandler = asyncHandler(async (request, response) => {
  const locale = getRequestedLocale(request);
  const includeDrafts = getIncludeDrafts(request);
  const articles = await listArticles(locale, { includeDrafts });
  response.status(200).json({
    items: articles,
    includeDrafts,
    locale: {
      requested: locale,
      default: localeConfig.defaultLocale,
      supported: supportedLocales,
    },
  });
});

const getArticleHandler = asyncHandler(async (request, response) => {
  const article = await getArticleById(
    request.params.id,
    getRequestedLocale(request),
    {
      includeDrafts: getIncludeDrafts(request),
    },
  );

  if (!article) {
    throw new ContentNotFoundError("Article not found.");
  }

  response.status(200).json(article);
});

const createArticleHandler = asyncHandler(async (request, response) => {
  const article = await createArticle(
    request.body,
    getRequestedLocale(request),
  );
  response.status(201).json(article);
});

const updateArticleHandler = asyncHandler(async (request, response) => {
  const article = await updateArticle(
    request.params.id,
    request.body,
    getRequestedLocale(request),
  );
  response.status(200).json(article);
});

const deleteArticleHandler = asyncHandler(async (request, response) => {
  await deleteArticle(request.params.id);
  response.status(204).send();
});

const listMediaHandler = asyncHandler(async (_request, response) => {
  const mediaAssets = await listMediaAssets();
  response.status(200).json({ items: mediaAssets });
});

const getMediaHandler = asyncHandler(async (request, response) => {
  const mediaAsset = await getMediaAssetById(request.params.id);

  if (!mediaAsset) {
    throw new ContentNotFoundError("Media asset not found.");
  }

  response.status(200).json(mediaAsset);
});

const uploadMediaHandler = asyncHandler(async (request, response) => {
  const uploadKind = getUploadKind(request);
  const filename = getUploadFilename(request);
  const mimeType = getUploadMimeType(request);

  validateUploadMimeType(uploadKind, mimeType);

  if (!Buffer.isBuffer(request.body) || request.body.length === 0) {
    throw new ContentValidationError(
      "Upload body must contain a non-empty file.",
    );
  }

  if (request.body.length > getUploadMaxBytes()) {
    throw new ContentValidationError(
      `Upload exceeds the ${getUploadMaxBytes()} byte limit.`,
    );
  }

  const relativeStoragePath = buildRelativeStoragePath(uploadKind, filename);
  const absoluteStoragePath = resolveStoragePath(relativeStoragePath);

  await mkdir(path.dirname(absoluteStoragePath), { recursive: true });
  await writeFile(absoluteStoragePath, request.body);

  try {
    const mediaAsset = await createMediaAsset({
      kind: uploadKind,
      originalName: filename,
      fileName: filename,
      mimeType,
      sizeBytes: request.body.length,
      storagePath: relativeStoragePath,
    });

    response.status(201).json(mediaAsset);
  } catch (error) {
    await unlink(absoluteStoragePath).catch(() => {});
    throw error;
  }
});

const getMediaFileHandler = asyncHandler(async (request, response) => {
  const mediaAsset = await getMediaAssetById(request.params.id);

  if (!mediaAsset) {
    throw new ContentNotFoundError("Media asset not found.");
  }

  const absoluteStoragePath = resolveStoragePath(mediaAsset.storagePath);

  try {
    await access(absoluteStoragePath);
  } catch {
    throw new ContentNotFoundError("Uploaded file is missing from storage.");
  }

  const dispositionType = mediaAsset.kind === "image" ? "inline" : "attachment";
  const safeFilename = mediaAsset.originalName.replace(/"/g, "");

  response.setHeader("Content-Type", mediaAsset.mimeType);
  response.setHeader("Content-Length", `${mediaAsset.sizeBytes}`);
  response.setHeader(
    "Content-Disposition",
    `${dispositionType}; filename="${safeFilename}"`,
  );

  response.sendFile(absoluteStoragePath);
});

const deleteMediaHandler = asyncHandler(async (request, response) => {
  const mediaAsset = await deleteMediaAsset(request.params.id);

  if (!mediaAsset) {
    throw new ContentNotFoundError("Media asset not found.");
  }

  await unlink(resolveStoragePath(mediaAsset.storagePath)).catch(() => {});

  response.status(204).send();
});

const contentErrorHandler: ErrorRequestHandler = (
  error,
  _request,
  response,
) => {
  if (error instanceof ContentValidationError) {
    response.status(400).json({
      error: error.name,
      message: error.message,
      details: error.details ?? [],
    });
    return;
  }

  if (error instanceof ContentNotFoundError) {
    response.status(404).json({
      error: error.name,
      message: error.message,
    });
    return;
  }

  if (error instanceof ContentConflictError) {
    response.status(409).json({
      error: error.name,
      message: error.message,
    });
    return;
  }

  contentLogger.error("Unexpected content API error", {
    error,
  });
  response.status(500).json({
    error: "InternalServerError",
    message: "Unexpected error while handling content request.",
  });
};

const contentRouter = Router();

contentRouter.get("/schema", schemaHandler);

contentRouter.get("/articles", listArticlesHandler);
contentRouter.get("/articles/:id", getArticleHandler);
contentRouter.post("/articles", createArticleHandler);
contentRouter.patch("/articles/:id", updateArticleHandler);
contentRouter.delete("/articles/:id", deleteArticleHandler);

contentRouter.get("/media", listMediaHandler);
contentRouter.get("/media/:id", getMediaHandler);
contentRouter.get("/media/:id/file", getMediaFileHandler);
contentRouter.post(
  "/media",
  express.raw({
    type: "*/*",
    limit: getUploadMaxBytes(),
  }),
  uploadMediaHandler,
);
contentRouter.delete("/media/:id", deleteMediaHandler);

contentRouter.use(contentErrorHandler);

export { contentRouter };
