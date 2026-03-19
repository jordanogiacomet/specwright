/**
 * @type {import('node-pg-migrate').ColumnDefinitions | undefined}
 */
export const shorthands = undefined;

/**
 * @param pgm {import('node-pg-migrate').MigrationBuilder}
 * @param run {() => void | undefined}
 * @returns {Promise<void> | void}
 */
export const up = (pgm) => {
  pgm.createTable("users", {
    id: {
      type: "text",
      primaryKey: true,
    },
    email: {
      type: "text",
      notNull: true,
      unique: true,
    },
    password_hash: {
      type: "text",
      notNull: true,
    },
    created_at: {
      type: "timestamptz",
      notNull: true,
      default: pgm.func("current_timestamp"),
    },
  });

  pgm.addConstraint("users", "users_email_lowercase_check", {
    check: "email = lower(email)",
  });
  pgm.addConstraint("users", "users_email_length_check", {
    check: "char_length(btrim(email)) BETWEEN 3 AND 320",
  });
  pgm.addConstraint("users", "users_password_hash_present_check", {
    check: "char_length(password_hash) > 0",
  });

  pgm.createIndex("users", "created_at");

  pgm.createTable("auth_sessions", {
    id: {
      type: "text",
      primaryKey: true,
    },
    user_id: {
      type: "text",
      notNull: true,
      references: "users",
      onDelete: "CASCADE",
    },
    created_at: {
      type: "timestamptz",
      notNull: true,
      default: pgm.func("current_timestamp"),
    },
    expires_at: {
      type: "timestamptz",
      notNull: true,
    },
  });

  pgm.addConstraint("auth_sessions", "auth_sessions_expiry_check", {
    check: "expires_at > created_at",
  });

  pgm.createIndex("auth_sessions", "user_id");
  pgm.createIndex("auth_sessions", "expires_at");
};

/**
 * @param pgm {import('node-pg-migrate').MigrationBuilder}
 * @param run {() => void | undefined}
 * @returns {Promise<void> | void}
 */
export const down = (pgm) => {
  pgm.dropTable("auth_sessions");
  pgm.dropTable("users");
};
