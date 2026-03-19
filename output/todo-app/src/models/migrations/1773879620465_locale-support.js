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
    default_locale: {
      type: "text",
      default: "en",
    },
    title_translations: {
      type: "jsonb",
      default: pgm.func(`'{}'::jsonb`),
    },
    excerpt_translations: {
      type: "jsonb",
      default: pgm.func(`'{}'::jsonb`),
    },
    body_translations: {
      type: "jsonb",
      default: pgm.func(`'{}'::jsonb`),
    },
  });

  pgm.sql(`
    UPDATE articles
    SET
      default_locale = COALESCE(default_locale, 'en'),
      title_translations = COALESCE(title_translations, '{}'::jsonb),
      excerpt_translations = COALESCE(excerpt_translations, '{}'::jsonb),
      body_translations = COALESCE(body_translations, '{}'::jsonb)
  `);

  pgm.alterColumn("articles", "default_locale", {
    notNull: true,
    default: "en",
  });
  pgm.alterColumn("articles", "title_translations", {
    notNull: true,
    default: pgm.func(`'{}'::jsonb`),
  });
  pgm.alterColumn("articles", "excerpt_translations", {
    notNull: true,
    default: pgm.func(`'{}'::jsonb`),
  });
  pgm.alterColumn("articles", "body_translations", {
    notNull: true,
    default: pgm.func(`'{}'::jsonb`),
  });

  pgm.addConstraint("articles", "articles_default_locale_check", {
    check: "default_locale IN ('en', 'pt')",
  });
  pgm.addConstraint("articles", "articles_title_translations_object_check", {
    check: "jsonb_typeof(title_translations) = 'object'",
  });
  pgm.addConstraint("articles", "articles_excerpt_translations_object_check", {
    check: "jsonb_typeof(excerpt_translations) = 'object'",
  });
  pgm.addConstraint("articles", "articles_body_translations_object_check", {
    check: "jsonb_typeof(body_translations) = 'object'",
  });
};

/**
 * @param pgm {import('node-pg-migrate').MigrationBuilder}
 * @param run {() => void | undefined}
 * @returns {Promise<void> | void}
 */
export const down = (pgm) => {
  pgm.dropConstraint("articles", "articles_body_translations_object_check");
  pgm.dropConstraint("articles", "articles_excerpt_translations_object_check");
  pgm.dropConstraint("articles", "articles_title_translations_object_check");
  pgm.dropConstraint("articles", "articles_default_locale_check");
  pgm.dropColumns("articles", [
    "default_locale",
    "title_translations",
    "excerpt_translations",
    "body_translations",
  ]);
};
