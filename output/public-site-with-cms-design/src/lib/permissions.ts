import type { Access, FieldAccess, PayloadRequest, Where } from "payload";

export const roleValues = ["admin", "user"] as const;

export type UserRole = (typeof roleValues)[number];

export const adminRole: UserRole = "admin";
export const defaultUserRole: UserRole = "user";

type UserLike =
  | {
      id?: number | string;
      role?: unknown;
    }
  | null
  | undefined;

function hasUserId(user: UserLike): user is { id: number | string; role?: unknown } {
  return typeof user?.id !== "undefined";
}

function sameUserId(left: number | string, right: number | string): boolean {
  return String(left) === String(right);
}

export function getUserRole(user: UserLike): UserRole {
  return user?.role === adminRole ? adminRole : defaultUserRole;
}

export function hasRole(user: UserLike, role: UserRole): boolean {
  return getUserRole(user) === role;
}

export function isAdminRequest(req: Pick<PayloadRequest, "user">): boolean {
  return hasRole(req.user as UserLike, adminRole);
}

export function canAccessAdminPanel({
  req,
}: {
  req: PayloadRequest;
}): boolean {
  return isAdminRequest(req);
}

export const isAdmin: Access = ({ req }) => isAdminRequest(req);

export const isAdminOrSelf: Access = ({ req }): boolean | Where => {
  if (isAdminRequest(req)) {
    return true;
  }

  const user = req.user as UserLike;

  if (!hasUserId(user)) {
    return false;
  }

  return {
    id: {
      equals: user.id,
    },
  };
};

export const canReadRoleField: FieldAccess = ({ doc, id, req }) => {
  if (isAdminRequest(req)) {
    return true;
  }

  const user = req.user as UserLike;
  const documentId = typeof id !== "undefined" ? id : doc?.id;

  return Boolean(
    hasUserId(user) &&
      typeof documentId !== "undefined" &&
      sameUserId(user.id, documentId),
  );
};

export const canManageRoles: FieldAccess = ({ req }) => isAdminRequest(req);

type RoleAuthorizationResult =
  | {
      ok: true;
    }
  | {
      ok: false;
      message: string;
      status: 401 | 403;
    };

export function requireRole(
  user: UserLike,
  role: UserRole,
): RoleAuthorizationResult {
  if (!hasUserId(user)) {
    return {
      ok: false,
      message: "Authentication required.",
      status: 401,
    };
  }

  if (!hasRole(user, role)) {
    return {
      ok: false,
      message: `${role} role required.`,
      status: 403,
    };
  }

  return {
    ok: true,
  };
}
