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
  pgm.addColumns("articles", {
    publication_status: {
      type: "text",
      default: "published",
    },
    publish_at: {
      type: "timestamptz",
    },
    published_at: {
      type: "timestamptz",
    },
  });

  pgm.sql(`
    UPDATE articles
    SET
      publication_status = COALESCE(publication_status, 'published'),
      published_at = COALESCE(published_at, created_at)
  `);

  pgm.alterColumn("articles", "publication_status", {
    notNull: true,
    default: "published",
  });

  pgm.addConstraint("articles", "articles_publication_status_check", {
    check: "publication_status IN ('draft', 'published')",
  });

  pgm.createIndex("articles", ["publication_status", "publish_at"], {
    name: "articles_publication_status_publish_at_idx",
  });
  pgm.createIndex("articles", "published_at");
};

/**
 * @param pgm {import('node-pg-migrate').MigrationBuilder}
 * @param run {() => void | undefined}
 * @returns {Promise<void> | void}
 */
export const down = (pgm) => {
  pgm.dropIndex("articles", "published_at");
  pgm.dropIndex("articles", ["publication_status", "publish_at"], {
    name: "articles_publication_status_publish_at_idx",
  });
  pgm.dropConstraint("articles", "articles_publication_status_check");
  pgm.dropColumns("articles", [
    "publication_status",
    "publish_at",
    "published_at",
  ]);
};
