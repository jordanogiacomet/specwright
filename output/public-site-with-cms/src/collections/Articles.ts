import type {
  CollectionBeforeChangeHook,
  CollectionConfig,
  TextFieldSingleValidation,
} from "payload";
import { ValidationError } from "payload";

import type { Article } from "../payload-types.ts";

import { LOCALIZED_FIELD, withLocaleSupport } from "../lib/i18n.ts";
import {
  DRAFT_STATUS,
  PUBLISHED_STATUS,
  SCHEDULED_STATUS,
  buildContentReadAccess,
  buildContentUpdateAccess,
  canTransitionContentStatus,
  isScheduledPublishContext,
  resolveContentStatus,
} from "../lib/content-status.ts";
import {
  adminUsersOnly,
  editorialUsersOnly,
  getUserRole,
  isEditorialUser,
} from "../lib/permissions.ts";

const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const ARTICLES_COLLECTION_SLUG = "articles" as const;

const validateSlug: TextFieldSingleValidation = (value) => {
  if (!value) {
    return "Slug is required.";
  }

  if (!SLUG_PATTERN.test(value)) {
    return "Use lowercase letters, numbers, and hyphens only.";
  }

  return true;
};

const validateArticleWorkflow: CollectionBeforeChangeHook<Article> = ({
  context,
  data,
  operation,
  originalDoc,
  req,
}) => {
  const currentStatus = resolveContentStatus(originalDoc?.status, DRAFT_STATUS);
  const nextStatus = resolveContentStatus(
    data.status,
    operation === "create" ? DRAFT_STATUS : currentStatus,
  );
  const publishAt = data.publishAt ?? originalDoc?.publishAt ?? null;
  const isScheduledPublishJob = isScheduledPublishContext(context);

  if (operation === "create") {
    return {
      ...data,
      publishedAt: null,
      status: DRAFT_STATUS,
    };
  }

  if (
    originalDoc?.status === PUBLISHED_STATUS &&
    nextStatus === PUBLISHED_STATUS
  ) {
    throw new ValidationError({
      collection: ARTICLES_COLLECTION_SLUG,
      errors: [
        {
          message:
            "Published content must move to a new draft before further edits.",
          path: "status",
        },
      ],
      req,
    });
  }

  if (nextStatus === SCHEDULED_STATUS && !publishAt) {
    throw new ValidationError({
      collection: ARTICLES_COLLECTION_SLUG,
      errors: [
        {
          message: "Scheduled content must include a publish time.",
          path: "publishAt",
        },
      ],
      req,
    });
  }

  if (
    !isScheduledPublishJob &&
    !canTransitionContentStatus({
      from: currentStatus,
      to: nextStatus,
      user: req.user,
    })
  ) {
    const role = getUserRole(req.user);
    const roleLabel = role ?? "current";

    throw new ValidationError({
      collection: ARTICLES_COLLECTION_SLUG,
      errors: [
        {
          message: `The ${roleLabel} role cannot change content from ${currentStatus} to ${nextStatus}.`,
          path: "status",
        },
      ],
      req,
    });
  }

  return {
    ...data,
    publishedAt:
      nextStatus === PUBLISHED_STATUS
        ? (data.publishedAt ??
          originalDoc?.publishedAt ??
          new Date().toISOString())
        : (data.publishedAt ?? originalDoc?.publishedAt ?? null),
    status: nextStatus,
  };
};

export const Articles: CollectionConfig = withLocaleSupport({
  slug: ARTICLES_COLLECTION_SLUG,
  admin: {
    useAsTitle: "title",
    defaultColumns: ["title", "slug", "status", "updatedAt"],
    group: "Content",
  },
  access: {
    admin: ({ req }) => isEditorialUser(req.user),
    create: editorialUsersOnly,
    delete: adminUsersOnly,
    read: ({ req }) => buildContentReadAccess(req.user),
    update: ({ req }) => buildContentUpdateAccess(req.user),
  },
  defaultSort: "-updatedAt",
  fields: [
    {
      name: "title",
      type: "text",
      ...LOCALIZED_FIELD,
      required: true,
      minLength: 3,
      maxLength: 120,
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
      name: "excerpt",
      type: "textarea",
      ...LOCALIZED_FIELD,
      maxLength: 300,
    },
    {
      name: "body",
      type: "textarea",
      ...LOCALIZED_FIELD,
      required: true,
      minLength: 20,
    },
    {
      name: "status",
      type: "select",
      required: true,
      defaultValue: "draft",
      admin: {
        position: "sidebar",
      },
      options: [
        {
          label: "Draft",
          value: "draft",
        },
        {
          label: "In review",
          value: "in_review",
        },
        {
          label: "Published",
          value: "published",
        },
        {
          label: "Scheduled",
          value: "scheduled",
        },
        {
          label: "Archived",
          value: "archived",
        },
      ],
    },
    {
      name: "author",
      type: "relationship",
      relationTo: "users",
      required: true,
      admin: {
        position: "sidebar",
      },
      defaultValue: ({ user }) => user?.id,
    },
    {
      name: "publishedAt",
      type: "date",
      admin: {
        position: "sidebar",
        date: {
          pickerAppearance: "dayAndTime",
        },
      },
    },
    {
      name: "publishAt",
      type: "date",
      label: "Publish at",
      admin: {
        position: "sidebar",
        date: {
          pickerAppearance: "dayAndTime",
        },
      },
    },
    {
      name: "heroImage",
      type: "upload",
      relationTo: "media",
    },
    {
      name: "attachments",
      type: "upload",
      relationTo: "media",
      hasMany: true,
    },
    {
      name: "categories",
      type: "relationship",
      relationTo: "categories",
      hasMany: true,
      admin: {
        allowCreate: true,
      },
    },
  ],
  hooks: {
    beforeChange: [validateArticleWorkflow],
  },
});
