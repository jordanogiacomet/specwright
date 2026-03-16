import type { RequestContext, Where } from "payload";

import type { User } from "../payload-types.ts";
import {
  ADMIN_ROLE,
  EDITOR_ROLE,
  REVIEWER_ROLE,
  getUserRole,
  type UserRole,
} from "./permissions.ts";

export const CONTENT_STATUSES = [
  "draft",
  "in_review",
  "published",
  "scheduled",
  "archived",
] as const;

export type ContentStatus = (typeof CONTENT_STATUSES)[number];

export const DRAFT_STATUS: ContentStatus = "draft";
export const IN_REVIEW_STATUS: ContentStatus = "in_review";
export const PUBLISHED_STATUS: ContentStatus = "published";
export const SCHEDULED_STATUS: ContentStatus = "scheduled";
export const ARCHIVED_STATUS: ContentStatus = "archived";
export const PUBLISHED_CONTENT_STATUSES = [PUBLISHED_STATUS] as const;
export const SCHEDULED_PUBLISH_CONTEXT_FLAG = "scheduledPublishingJob" as const;

type UserLike = Partial<Pick<User, "id" | "role">> | null | undefined;
type ContentTransition = {
  from: ContentStatus;
  roles: readonly UserRole[];
  to: ContentStatus;
};

const CONTENT_STATUS_SET = new Set<ContentStatus>(CONTENT_STATUSES);
const REVIEWER_VISIBLE_STATUSES = [
  IN_REVIEW_STATUS,
  PUBLISHED_STATUS,
  SCHEDULED_STATUS,
  ARCHIVED_STATUS,
] as const;
const EDITOR_MUTABLE_STATUSES = [DRAFT_STATUS, IN_REVIEW_STATUS] as const;
const CONTENT_TRANSITIONS: readonly ContentTransition[] = [
  {
    from: DRAFT_STATUS,
    roles: [EDITOR_ROLE, ADMIN_ROLE],
    to: IN_REVIEW_STATUS,
  },
  {
    from: IN_REVIEW_STATUS,
    roles: [REVIEWER_ROLE, ADMIN_ROLE],
    to: DRAFT_STATUS,
  },
  {
    from: IN_REVIEW_STATUS,
    roles: [REVIEWER_ROLE, ADMIN_ROLE],
    to: PUBLISHED_STATUS,
  },
  {
    from: IN_REVIEW_STATUS,
    roles: [REVIEWER_ROLE, ADMIN_ROLE],
    to: SCHEDULED_STATUS,
  },
  {
    from: SCHEDULED_STATUS,
    roles: [REVIEWER_ROLE, ADMIN_ROLE],
    to: DRAFT_STATUS,
  },
  {
    from: SCHEDULED_STATUS,
    roles: [REVIEWER_ROLE, ADMIN_ROLE],
    to: PUBLISHED_STATUS,
  },
  {
    from: PUBLISHED_STATUS,
    roles: [ADMIN_ROLE],
    to: ARCHIVED_STATUS,
  },
] as const;

export const isScheduledPublishContext = (context: RequestContext): boolean =>
  context[SCHEDULED_PUBLISH_CONTEXT_FLAG] === true;

export const normalizeContentStatus = (
  value: unknown,
): ContentStatus | null => {
  if (typeof value !== "string") {
    return null;
  }

  return CONTENT_STATUS_SET.has(value as ContentStatus)
    ? (value as ContentStatus)
    : null;
};

export const resolveContentStatus = (
  value: unknown,
  fallback: ContentStatus = DRAFT_STATUS,
): ContentStatus => normalizeContentStatus(value) ?? fallback;

export const canTransitionContentStatus = ({
  from,
  to,
  user,
}: {
  from: ContentStatus;
  to: ContentStatus;
  user: UserLike;
}): boolean => {
  if (from === to) {
    return true;
  }

  const role = getUserRole(user);

  if (!role) {
    return false;
  }

  return CONTENT_TRANSITIONS.some(
    (transition) =>
      transition.from === from &&
      transition.to === to &&
      transition.roles.includes(role),
  );
};

export const buildContentReadAccess = (user: UserLike): true | Where => {
  const role = getUserRole(user);

  if (role === ADMIN_ROLE) {
    return true;
  }

  if (role === EDITOR_ROLE && user?.id) {
    return {
      or: [
        {
          status: {
            equals: PUBLISHED_STATUS,
          },
        },
        {
          author: {
            equals: user.id,
          },
        },
      ],
    };
  }

  if (role === REVIEWER_ROLE) {
    return {
      status: {
        in: [...REVIEWER_VISIBLE_STATUSES],
      },
    };
  }

  return {
    status: {
      equals: PUBLISHED_STATUS,
    },
  };
};

export const buildContentUpdateAccess = (
  user: UserLike,
): true | Where | false => {
  const role = getUserRole(user);

  if (role === ADMIN_ROLE) {
    return true;
  }

  if (role === REVIEWER_ROLE) {
    return {
      status: {
        in: [...REVIEWER_VISIBLE_STATUSES],
      },
    };
  }

  if (role === EDITOR_ROLE && user?.id) {
    return {
      and: [
        {
          author: {
            equals: user.id,
          },
        },
        {
          status: {
            in: [...EDITOR_MUTABLE_STATUSES],
          },
        },
      ],
    };
  }

  return false;
};
