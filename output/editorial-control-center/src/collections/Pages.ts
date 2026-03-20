import type { CollectionConfig } from "payload";

export const Pages: CollectionConfig = {
  slug: "pages",
  admin: {
    useAsTitle: "title",
  },
  fields: [
    {
      name: "title",
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
      name: "hero",
      type: "relationship",
      admin: {
        position: "sidebar",
      },
      relationTo: "media",
    },
    {
      name: "body_or_blocks",
      type: "blocks",
      blocks: [
        {
          slug: "content",
          fields: [
            {
              name: "content",
              type: "textarea",
              required: true,
            },
          ],
          labels: {
            plural: "Content Blocks",
            singular: "Content Block",
          },
        },
        {
          slug: "media",
          fields: [
            {
              name: "media",
              type: "relationship",
              relationTo: "media",
              required: true,
            },
          ],
          labels: {
            plural: "Media Blocks",
            singular: "Media Block",
          },
        },
      ],
    },
    {
      name: "seo_title",
      type: "text",
    },
    {
      name: "seo_description",
      type: "textarea",
    },
  ],
};
