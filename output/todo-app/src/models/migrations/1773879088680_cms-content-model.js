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
  pgm.createTable("media_assets", {
    id: {
      type: "text",
      primaryKey: true,
    },
    kind: {
      type: "text",
      notNull: true,
    },
    original_name: {
      type: "text",
      notNull: true,
    },
    file_name: {
      type: "text",
      notNull: true,
    },
    mime_type: {
      type: "text",
      notNull: true,
    },
    size_bytes: {
      type: "integer",
      notNull: true,
    },
    storage_path: {
      type: "text",
      notNull: true,
      unique: true,
    },
    created_at: {
      type: "timestamptz",
      notNull: true,
      default: pgm.func("current_timestamp"),
    },
  });

  pgm.addConstraint("media_assets", "media_assets_kind_check", {
    check: "kind IN ('image', 'file')",
  });
  pgm.addConstraint("media_assets", "media_assets_size_bytes_check", {
    check: "size_bytes > 0",
  });

  pgm.createTable("articles", {
    id: {
      type: "text",
      primaryKey: true,
    },
    slug: {
      type: "text",
      notNull: true,
      unique: true,
    },
    title: {
      type: "text",
      notNull: true,
    },
    excerpt: {
      type: "text",
      notNull: true,
    },
    body: {
      type: "text",
      notNull: true,
    },
    hero_image_id: {
      type: "text",
      references: "media_assets",
      onDelete: "SET NULL",
    },
    attachment_file_id: {
      type: "text",
      references: "media_assets",
      onDelete: "SET NULL",
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

  pgm.addConstraint("articles", "articles_slug_format_check", {
    check: "slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'",
  });
  pgm.addConstraint("articles", "articles_title_check", {
    check: "char_length(btrim(title)) BETWEEN 1 AND 160",
  });
  pgm.addConstraint("articles", "articles_excerpt_check", {
    check: "char_length(btrim(excerpt)) BETWEEN 1 AND 320",
  });
  pgm.addConstraint("articles", "articles_body_check", {
    check: "char_length(btrim(body)) BETWEEN 1 AND 20000",
  });

  pgm.createIndex("articles", "created_at");
  pgm.createIndex("articles", "updated_at");
  pgm.createIndex("media_assets", "kind");
};

/**
 * @param pgm {import('node-pg-migrate').MigrationBuilder}
 * @param run {() => void | undefined}
 * @returns {Promise<void> | void}
 */
export const down = (pgm) => {
  pgm.dropTable("articles");
  pgm.dropTable("media_assets");
};
