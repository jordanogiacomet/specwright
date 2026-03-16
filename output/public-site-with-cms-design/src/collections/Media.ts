import type {
  CollectionBeforeValidateHook,
  CollectionConfig,
  TextFieldValidation,
  TextareaFieldValidation,
} from "payload";
import { ValidationError } from "payload";

import { publicRead } from "../access/shared.ts";
import {
  createLocaleMetaField,
  validateLocalizedText,
} from "../lib/i18n.ts";
import { isAdmin } from "../lib/permissions.ts";

const mediaCollectionSlug = "media";
const imageAltTextLimit = 160;
const maxUploadFileSizeInBytes = 25 * 1024 * 1024;
const maxUploadFileSizeLabel = "25 MB";
const mediaUploadMimeTypes = [
  "image/*",
  "application/pdf",
  "text/plain",
  "application/zip",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
] as const;

function isImageMimeType(mimeType: string): boolean {
  return mimeType.startsWith("image/");
}

const validateUploadSize: CollectionBeforeValidateHook = ({ req }) => {
  if (!req.file) {
    return;
  }

  if (req.file.size <= maxUploadFileSizeInBytes) {
    return;
  }

  throw new ValidationError(
    {
      collection: mediaCollectionSlug,
      errors: [
        {
          message: `Files must be ${maxUploadFileSizeLabel} or smaller.`,
          path: "file",
        },
      ],
    },
    req.t,
  );
};

const getAdminThumbnail = ({
  doc,
}: {
  doc: Record<string, unknown>;
}): false | null | string => {
  const mimeType = typeof doc.mimeType === "string" ? doc.mimeType : "";
  const url = typeof doc.url === "string" ? doc.url : null;

  if (!isImageMimeType(mimeType) || !url) {
    return null;
  }

  return url;
};

const validateAltText: TextFieldValidation = (value, { req, siblingData }) => {
  const siblingRecord = siblingData as { mimeType?: unknown } | undefined;
  const mimeType =
    typeof siblingRecord?.mimeType === "string" ? siblingRecord.mimeType : "";
  const isImage = isImageMimeType(mimeType);

  return validateLocalizedText(value, req, {
    fieldLabel: "Alt text",
    maxLength: imageAltTextLimit,
    requiredInDefaultLocale: isImage,
  });
};

const validateCaption: TextareaFieldValidation = (value, { req }) => {
  return validateLocalizedText(value, req, {
    fieldLabel: "Caption",
    maxLength: 300,
  });
};

export const Media: CollectionConfig = {
  slug: mediaCollectionSlug,
  access: {
    create: isAdmin,
    delete: isAdmin,
    read: publicRead,
    update: isAdmin,
  },
  admin: {
    defaultColumns: ["filename", "alt", "mimeType", "updatedAt"],
    group: "Content",
    useAsTitle: "filename",
  },
  fields: [
    {
      name: "alt",
      type: "text",
      admin: {
        description: "Required for image uploads and optional for non-image files.",
      },
      localized: true,
      maxLength: imageAltTextLimit,
      validate: validateAltText,
    },
    {
      name: "caption",
      type: "textarea",
      localized: true,
      maxLength: 300,
      validate: validateCaption,
    },
    createLocaleMetaField(),
  ],
  labels: {
    plural: "Media",
    singular: "Media Item",
  },
  hooks: {
    beforeValidate: [validateUploadSize],
  },
  upload: {
    adminThumbnail: getAdminThumbnail,
    displayPreview: true,
    mimeTypes: [...mediaUploadMimeTypes],
    staticDir: "media",
  },
};
