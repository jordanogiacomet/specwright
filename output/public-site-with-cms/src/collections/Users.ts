import type { CollectionBeforeChangeHook, CollectionConfig } from "payload";

import type { User } from "../payload-types.ts";

import {
  ADMIN_ROLE,
  DEFAULT_USER_ROLE,
  USER_ROLES,
  adminOrCurrentUser,
  adminPanelAccess,
  getUserRole,
  isAdminUser,
} from "../lib/permissions.ts";

const USERS_SLUG = "users" as const;
const USER_ROLE_LABELS: Record<User["role"], string> = {
  admin: "Admin",
  editor: "Editor",
  reviewer: "Reviewer",
  user: "User",
};

const normalizeRequestedRole = (value: unknown) =>
  typeof value === "string"
    ? getUserRole({ role: value as User["role"] })
    : null;

const assignRoleOnWrite: CollectionBeforeChangeHook<User> = async ({
  data,
  operation,
  originalDoc,
  req,
}) => {
  const requestedRole = normalizeRequestedRole(data.role);

  if (operation === "create") {
    const { totalDocs } = await req.payload.count({
      collection: USERS_SLUG,
      overrideAccess: true,
      req,
    });

    if (totalDocs === 0) {
      return {
        ...data,
        role: ADMIN_ROLE,
      };
    }

    return {
      ...data,
      role:
        isAdminUser(req.user) && requestedRole
          ? requestedRole
          : DEFAULT_USER_ROLE,
    };
  }

  if (!isAdminUser(req.user)) {
    return {
      ...data,
      role: originalDoc?.role ?? DEFAULT_USER_ROLE,
    };
  }

  return {
    ...data,
    role: requestedRole ?? originalDoc?.role ?? DEFAULT_USER_ROLE,
  };
};

export const Users: CollectionConfig = {
  slug: USERS_SLUG,
  admin: {
    useAsTitle: "email",
    defaultColumns: ["email", "role", "updatedAt"],
  },
  access: {
    admin: adminPanelAccess,
    create: () => true,
    delete: () => false,
    read: adminOrCurrentUser,
    update: adminOrCurrentUser,
  },
  auth: true,
  fields: [
    {
      name: "role",
      type: "select",
      required: true,
      defaultValue: DEFAULT_USER_ROLE,
      index: true,
      options: USER_ROLES.map((role) => ({
        label: USER_ROLE_LABELS[role],
        value: role,
      })),
      admin: {
        position: "sidebar",
      },
    },
  ],
  hooks: {
    beforeChange: [assignRoleOnWrite],
  },
};
