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
  pgm.createTable("todos", {
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
    title: {
      type: "text",
      notNull: true,
    },
    description: {
      type: "text",
    },
    completed: {
      type: "boolean",
      notNull: true,
      default: false,
    },
    due_date: {
      type: "timestamptz",
    },
    priority: {
      type: "text",
      notNull: true,
      default: "medium",
    },
    created_at: {
      type: "timestamptz",
      notNull: true,
      default: pgm.func("current_timestamp"),
    },
    updated_at: {
      type: "timestamptz",
      notNull: true,
      default: pgm.func("current_timestamp"),
    },
  });

  pgm.addConstraint("todos", "todos_title_present_check", {
    check: "char_length(btrim(title)) > 0",
  });
  pgm.addConstraint("todos", "todos_priority_check", {
    check: "priority IN ('low', 'medium', 'high')",
  });
  pgm.addConstraint("todos", "todos_updated_at_check", {
    check: "updated_at >= created_at",
  });

  pgm.createIndex("todos", ["user_id", "created_at"]);
  pgm.createIndex("todos", ["user_id", "completed"]);
  pgm.createIndex("todos", ["user_id", "priority"]);
  pgm.createIndex("todos", ["user_id", "due_date"]);
};

/**
 * @param pgm {import('node-pg-migrate').MigrationBuilder}
 * @param run {() => void | undefined}
 * @returns {Promise<void> | void}
 */
export const down = (pgm) => {
  pgm.dropTable("todos");
};
