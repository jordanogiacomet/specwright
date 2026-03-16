import type { CollectionConfig, TextFieldSingleValidation } from "payload";

import { LOCALIZED_FIELD, withLocaleSupport } from "../lib/i18n.ts";

const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const validateSlug: TextFieldSingleValidation = (value) => {
  if (!value) {
    return "Slug is required.";
  }

  if (!SLUG_PATTERN.test(value)) {
    return "Use lowercase letters, numbers, and hyphens only.";
  }

  return true;
};

export const Categories: CollectionConfig = withLocaleSupport({
  slug: "categories",
  admin: {
    useAsTitle: "name",
    defaultColumns: ["name", "slug", "updatedAt"],
    group: "Content",
  },
  defaultSort: "name",
  fields: [
    {
      name: "name",
      type: "text",
      ...LOCALIZED_FIELD,
      required: true,
      unique: true,
      minLength: 2,
      maxLength: 80,
    },
    {
      name: "slug",
      type: "text",
      required: true,
      unique: true,
      index: true,
      minLength: 2,
      maxLength: 96,
      validate: validateSlug,
    },
    {
      name: "description",
      type: "textarea",
      ...LOCALIZED_FIELD,
      maxLength: 500,
    },
  ],
});
