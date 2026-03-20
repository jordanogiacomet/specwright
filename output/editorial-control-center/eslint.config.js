const { FlatCompat } = require("@eslint/eslintrc");

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

module.exports = [
  {
    ignores: ["eslint.config.js", ".next/**", "node_modules/**", "dist/**", "build/**", "coverage/**"],
  },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
];
