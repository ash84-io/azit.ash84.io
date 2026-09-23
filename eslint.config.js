// ESLint 9 flat config. Kept dependency-free so `npx eslint@9` works without an install step.
const browserGlobals = {
  window: "readonly",
  document: "readonly",
  fetch: "readonly",
  console: "readonly",
  matchMedia: "readonly",
  requestAnimationFrame: "readonly",
  history: "readonly",
  location: "readonly",
  Image: "readonly",
  URL: "readonly",
};

export default [
  {
    files: ["site/js/**/*.js", "tests/js/**/*.mjs"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: browserGlobals,
    },
    rules: {
      "no-undef": "error",
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "prefer-const": "error",
      eqeqeq: "error",
      "no-var": "error",
      curly: "error",
    },
  },
];
