import type { Access } from "payload";

export const allowAnyone: Access = () => true;

export const isAuthenticated: Access = ({ req }) => Boolean(req.user);

export const isSelf: Access = ({ req }) => {
  if (!req.user || typeof req.user.id === "undefined") {
    return false;
  }

  return {
    id: {
      equals: req.user.id,
    },
  };
};

export const publicRead: Access = allowAnyone;
