import {
  Forbidden,
  type Access,
  type PayloadRequest,
  type Where,
} from "payload";

import type { User } from "../payload-types.ts";

export const USER_ROLES = ["admin", "editor", "reviewer", "user"] as const;

export type UserRole = (typeof USER_ROLES)[number];

export const ADMIN_ROLE: UserRole = "admin";
export const EDITOR_ROLE: UserRole = "editor";
export const REVIEWER_ROLE: UserRole = "reviewer";
export const DEFAULT_USER_ROLE: UserRole = "user";
export const EDITORIAL_ROLES = [
  ADMIN_ROLE,
  EDITOR_ROLE,
  REVIEWER_ROLE,
] as const;
export const REVIEWER_OR_ADMIN_ROLES = [ADMIN_ROLE, REVIEWER_ROLE] as const;

type UserLike = Partial<Pick<User, "id" | "role">> | null | undefined;

const USER_ROLE_SET = new Set<UserRole>(USER_ROLES);

export const getUserRole = (user: UserLike): UserRole | null => {
  if (!user || typeof user.role !== "string") {
    return null;
  }

  return USER_ROLE_SET.has(user.role as UserRole)
    ? (user.role as UserRole)
    : null;
};

export const hasRole = (
  user: UserLike,
  roles: readonly UserRole[],
): boolean => {
  const role = getUserRole(user);

  return role ? roles.includes(role) : false;
};

export const isAdminUser = (user: UserLike): boolean =>
  hasRole(user, [ADMIN_ROLE]);
export const isEditorialUser = (user: UserLike): boolean =>
  hasRole(user, EDITORIAL_ROLES);
export const isReviewerOrAdminUser = (user: UserLike): boolean =>
  hasRole(user, REVIEWER_OR_ADMIN_ROLES);

const scopeToCurrentUser = (user: UserLike): Where | false => {
  if (!user?.id) {
    return false;
  }

  return {
    id: {
      equals: user.id,
    },
  };
};

export const authenticatedUsersOnly: Access = ({ req }) => Boolean(req.user);

export const adminUsersOnly: Access = ({ req }) =>
  isAdminUser(req.user as UserLike);
export const editorialUsersOnly: Access = ({ req }) =>
  isEditorialUser(req.user as UserLike);

export const adminOrCurrentUser: Access = ({ req }) => {
  if (isAdminUser(req.user as UserLike)) {
    return true;
  }

  return scopeToCurrentUser(req.user as UserLike);
};

export const adminPanelAccess = ({ req }: { req: PayloadRequest }): boolean => {
  if (!req.user) {
    return false;
  }

  if (!isAdminUser(req.user as UserLike)) {
    throw new Forbidden(req.t);
  }

  return true;
};
