import type { CollectionConfig } from "payload";

export const Authors: CollectionConfig = {
  slug: "authors",
  admin: {
    useAsTitle: "name",
  },
  fields: [
    {
      name: "name",
      type: "text",
      required: true,
    },
    {
      name: "slug",
      type: "text",
      admin: {
        position: "sidebar",
      },
      index: true,
      required: true,
      unique: true,
    },
    {
      name: "bio",
      type: "textarea",
    },
    {
      name: "avatar",
      type: "relationship",
      admin: {
        position: "sidebar",
      },
      relationTo: "media",
    },
  ],
};
