import type { CollectionBeforeChangeHook, CollectionConfig } from "payload";

import { allowAnyone } from "../access/shared.ts";
import {
  adminRole,
  canAccessAdminPanel,
  canManageRoles,
  canReadRoleField,
  defaultUserRole,
  getUserRole,
  isAdminOrSelf,
  isAdminRequest,
  roleValues,
} from "../lib/permissions.ts";

const ensureRoleAssignment: CollectionBeforeChangeHook = async ({
  data,
  operation,
  originalDoc,
  req,
}) => {
  const nextData = { ...data };
  const adminRequest = isAdminRequest(req);

  if (operation === "create") {
    const existingUsers = await req.payload.find({
      collection: "users",
      depth: 0,
      limit: 1,
      overrideAccess: true,
      pagination: false,
    });

    if (existingUsers.docs.length === 0) {
      nextData.role = adminRole;
      return nextData;
    }

    if (!adminRequest || typeof nextData.role === "undefined") {
      nextData.role = defaultUserRole;
    }

    return nextData;
  }

  if (!adminRequest) {
    nextData.role = getUserRole(originalDoc);
    return nextData;
  }

  if (typeof nextData.role === "undefined") {
    nextData.role = getUserRole(originalDoc);
  }

  return nextData;
};

export const Users: CollectionConfig = {
  slug: "users",
  access: {
    admin: canAccessAdminPanel,
    create: allowAnyone,
    delete: isAdminOrSelf,
    read: isAdminOrSelf,
    unlock: isAdminOrSelf,
    update: isAdminOrSelf,
  },
  admin: {
    defaultColumns: ["email", "role", "updatedAt", "createdAt"],
    group: "Administration",
    useAsTitle: "email",
  },
  auth: {
    tokenExpiration: 7200,
    useSessions: true,
  },
  hooks: {
    beforeChange: [ensureRoleAssignment],
  },
  fields: [
    {
      name: "role",
      type: "select",
      access: {
        read: canReadRoleField,
        update: canManageRoles,
      },
      admin: {
        description: "Admins can access the CMS admin and manage user roles.",
        position: "sidebar",
      },
      defaultValue: defaultUserRole,
      options: roleValues.map((role) => ({
        label: role === adminRole ? "Admin" : "User",
        value: role,
      })),
      required: true,
      saveToJWT: true,
    },
  ],
};
