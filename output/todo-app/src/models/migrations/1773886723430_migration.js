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
  pgm.addColumn("todos", {
    assignee_id: {
      type: "text",
      references: "users",
      onDelete: "SET NULL",
    },
  });

  pgm.createIndex("todos", ["assignee_id", "created_at"]);
  pgm.createIndex("todos", ["user_id", "assignee_id"]);
};

/**
 * @param pgm {import('node-pg-migrate').MigrationBuilder}
 * @param run {() => void | undefined}
 * @returns {Promise<void> | void}
 */
export const down = (pgm) => {
  pgm.dropColumn("todos", "assignee_id");
};
