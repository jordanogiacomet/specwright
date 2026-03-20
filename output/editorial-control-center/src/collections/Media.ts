import type { CollectionConfig } from "payload";

export const Media: CollectionConfig = {
  slug: "media",
  admin: {
    useAsTitle: "filename",
  },
  fields: [],
  upload: {
    mimeTypes: ["image/*", "application/pdf"],
  },
};
