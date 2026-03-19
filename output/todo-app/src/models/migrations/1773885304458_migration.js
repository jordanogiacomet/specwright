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
  pgm.addColumns("todos", {
    status: {
      type: "text",
      default: "pending",
    },
    last_status_transition_from: {
      type: "text",
    },
    last_status_transition_at: {
      type: "timestamptz",
    },
  });

  pgm.sql(`
    UPDATE todos
    SET status = CASE
      WHEN completed THEN 'completed'
      ELSE 'pending'
    END
  `);

  pgm.alterColumn("todos", "status", {
    notNull: true,
    default: "pending",
  });

  pgm.addConstraint("todos", "todos_status_check", {
    check: "status IN ('pending', 'in_progress', 'completed')",
  });
  pgm.addConstraint("todos", "todos_last_status_transition_from_check", {
    check:
      "last_status_transition_from IS NULL OR last_status_transition_from IN ('pending', 'in_progress', 'completed')",
  });
};

/**
 * @param pgm {import('node-pg-migrate').MigrationBuilder}
 * @param run {() => void | undefined}
 * @returns {Promise<void> | void}
 */
export const down = (pgm) => {
  pgm.dropConstraint("todos", "todos_last_status_transition_from_check", {
    ifExists: true,
  });
  pgm.dropConstraint("todos", "todos_status_check", {
    ifExists: true,
  });
  pgm.dropColumns("todos", [
    "status",
    "last_status_transition_from",
    "last_status_transition_at",
  ]);
};
