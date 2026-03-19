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
  pgm.createTable("notification_preferences", {
    user_id: {
      type: "text",
      primaryKey: true,
      references: "users",
      onDelete: "CASCADE",
    },
    notifications_enabled: {
      type: "boolean",
      notNull: true,
      default: true,
    },
    minimum_priority: {
      type: "text",
      notNull: true,
      default: "normal",
    },
    updated_at: {
      type: "timestamptz",
      notNull: true,
      default: pgm.func("current_timestamp"),
    },
  });

  pgm.addConstraint(
    "notification_preferences",
    "notification_preferences_minimum_priority_check",
    {
      check: "minimum_priority IN ('low', 'normal', 'high', 'critical')",
    },
  );

  pgm.createTable("notifications", {
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
    event_key: {
      type: "text",
      notNull: true,
    },
    type: {
      type: "text",
      notNull: true,
    },
    priority: {
      type: "text",
      notNull: true,
      default: "normal",
    },
    title: {
      type: "text",
      notNull: true,
    },
    body: {
      type: "text",
      notNull: true,
    },
    metadata: {
      type: "jsonb",
      notNull: true,
      default: pgm.func("'{}'::jsonb"),
    },
    is_read: {
      type: "boolean",
      notNull: true,
      default: false,
    },
    read_at: {
      type: "timestamptz",
    },
    created_at: {
      type: "timestamptz",
      notNull: true,
      default: pgm.func("current_timestamp"),
    },
  });

  pgm.addConstraint("notifications", "notifications_priority_check", {
    check: "priority IN ('low', 'normal', 'high', 'critical')",
  });
  pgm.addConstraint("notifications", "notifications_read_state_check", {
    check:
      "(is_read = FALSE AND read_at IS NULL) OR (is_read = TRUE AND read_at IS NOT NULL)",
  });
  pgm.addConstraint("notifications", "notifications_event_key_present_check", {
    check: "char_length(btrim(event_key)) > 0",
  });
  pgm.addConstraint("notifications", "notifications_type_present_check", {
    check: "char_length(btrim(type)) > 0",
  });
  pgm.addConstraint("notifications", "notifications_title_present_check", {
    check: "char_length(btrim(title)) > 0",
  });
  pgm.addConstraint("notifications", "notifications_body_present_check", {
    check: "char_length(btrim(body)) > 0",
  });

  pgm.createIndex("notifications", ["user_id", "created_at"]);
  pgm.createIndex("notifications", ["user_id", "is_read"]);
};

/**
 * @param pgm {import('node-pg-migrate').MigrationBuilder}
 * @param run {() => void | undefined}
 * @returns {Promise<void> | void}
 */
export const down = (pgm) => {
  pgm.dropTable("notifications");
  pgm.dropTable("notification_preferences");
};
