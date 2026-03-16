import type {
  CollectionConfig,
  TextFieldValidation,
  TextareaFieldValidation,
} from "payload";

import { publicRead } from "../access/shared.ts";
import {
  createLocaleMetaField,
  validateLocalizedText,
} from "../lib/i18n.ts";
import { isAdmin } from "../lib/permissions.ts";

const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const validateSlug: TextFieldValidation = (value) => {
  if (typeof value !== "string" || value.trim().length === 0) {
    return "Slug is required.";
  }

  if (!slugPattern.test(value)) {
    return "Slug must use lowercase letters, numbers, and hyphens only.";
  }

  return true;
};

const validateTitle: TextFieldValidation = (value, { req }) => {
  return validateLocalizedText(value, req, {
    fieldLabel: "Title",
    maxLength: 120,
    minLength: 5,
    requiredInDefaultLocale: true,
  });
};

const validateExcerpt: TextareaFieldValidation = (value, { req }) => {
  return validateLocalizedText(value, req, {
    fieldLabel: "Excerpt",
    maxLength: 300,
    minLength: 20,
    requiredInDefaultLocale: true,
  });
};

const validateBody: TextareaFieldValidation = (value, { req }) => {
  return validateLocalizedText(value, req, {
    fieldLabel: "Body",
    minLength: 50,
    requiredInDefaultLocale: true,
  });
};

export const Articles: CollectionConfig = {
  slug: "articles",
  access: {
    create: isAdmin,
    delete: isAdmin,
    read: publicRead,
    update: isAdmin,
  },
  admin: {
    defaultColumns: ["title", "slug", "author", "updatedAt"],
    group: "Content",
    useAsTitle: "title",
  },
  defaultSort: "-updatedAt",
  fields: [
    {
      name: "title",
      type: "text",
      localized: true,
      maxLength: 120,
      minLength: 5,
      validate: validateTitle,
    },
    {
      name: "slug",
      type: "text",
      admin: {
        description:
          "Lowercase URL segment using letters, numbers, and hyphens only.",
      },
      index: true,
      maxLength: 140,
      required: true,
      unique: true,
      validate: validateSlug,
    },
    {
      name: "excerpt",
      type: "textarea",
      localized: true,
      maxLength: 300,
      minLength: 20,
      validate: validateExcerpt,
    },
    {
      name: "body",
      type: "textarea",
      localized: true,
      minLength: 50,
      validate: validateBody,
    },
    {
      name: "author",
      type: "relationship",
      admin: {
        allowCreate: false,
      },
      relationTo: "users",
      required: true,
    },
    {
      name: "heroImage",
      type: "upload",
      admin: {
        description: "Primary image shown when this article is featured.",
      },
      filterOptions: {
        mimeType: {
          contains: "image/",
        },
      },
      relationTo: "media",
      required: true,
    },
    {
      name: "attachments",
      type: "upload",
      admin: {
        description: "Optional supporting files such as PDFs or downloadable assets.",
      },
      hasMany: true,
      relationTo: "media",
    },
    createLocaleMetaField(),
  ],
  labels: {
    plural: "Articles",
    singular: "Article",
  },
};
