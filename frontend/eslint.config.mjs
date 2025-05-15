import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import pluginReact from "eslint-plugin-react";
import { defineConfig } from "eslint/config";

export default defineConfig([
  // your base JS/TS rules
  {
    files: ["**/*.{js,mjs,cjs,ts,jsx,tsx}"],
    plugins: { js },
    extends: ["js/recommended"],
    // ← add settings here:
    settings: {
      react: {
        version: "detect",   // auto-detect from your installed react
      },
    },
  },

  // browser globals
  {
    files: ["**/*.{js,mjs,cjs,ts,jsx,tsx}"],
    languageOptions: { globals: globals.browser },
  },

  // TS rules
  tseslint.configs.recommended,

  // React rules
  pluginReact.configs.flat.recommended,
]);
