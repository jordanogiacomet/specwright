import path from "path";
import type { Access, CollectionBeforeValidateHook, CollectionConfig } from "payload";
import { ValidationError } from "payload";

import { LOCALIZED_FIELD, withLocaleSupport } from "../lib/i18n.ts";
import { authenticatedUsersOnly } from "../lib/permissions.ts";

const MEDIA_COLLECTION_SLUG = "media" as const;
const MAX_UPLOAD_FILE_SIZE_BYTES = 25 * 1024 * 1024;
const MEDIA_MIME_TYPES = [
  "image/*",
  "application/pdf",
  "application/zip",
  "text/plain",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
] as const;

const authenticatedMediaRead: Access = ({ isReadingStaticFile, req }) => {
  if (isReadingStaticFile) {
    return true;
  }

  return authenticatedUsersOnly({ req });
};

const validateUploadFileSize: CollectionBeforeValidateHook = ({ data, req }) => {
  if (!req.file || req.file.size <= MAX_UPLOAD_FILE_SIZE_BYTES) {
    return data;
  }

  throw new ValidationError({
    collection: MEDIA_COLLECTION_SLUG,
    errors: [
      {
        message: "Files must be 25 MB or smaller.",
        path: "file",
      },
    ],
    req,
  });
};

export const Media: CollectionConfig = withLocaleSupport({
  slug: MEDIA_COLLECTION_SLUG,
  admin: {
    useAsTitle: "filename",
    defaultColumns: ["filename", "mimeType", "filesize", "updatedAt"],
    group: "Media",
  },
  access: {
    create: authenticatedUsersOnly,
    delete: authenticatedUsersOnly,
    read: authenticatedMediaRead,
    update: authenticatedUsersOnly,
  },
  defaultSort: "-createdAt",
  fields: [
    {
      name: "alt",
      label: "Alt text",
      type: "text",
      ...LOCALIZED_FIELD,
      maxLength: 200,
    },
    {
      name: "uploadedBy",
      type: "relationship",
      relationTo: "users",
      admin: {
        position: "sidebar",
      },
      defaultValue: ({ user }) => user?.id,
    },
  ],
  hooks: {
    beforeValidate: [validateUploadFileSize],
  },
  upload: {
    staticDir: path.resolve(process.cwd(), "media"),
    adminThumbnail: "thumbnail",
    displayPreview: true,
    focalPoint: true,
    imageSizes: [
      {
        name: "thumbnail",
        width: 400,
        height: 300,
        fit: "cover",
      },
    ],
    mimeTypes: [...MEDIA_MIME_TYPES],
  },
});
