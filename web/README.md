# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:


## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.

## Chrome Extension

Built with Node 22, React, TypeScript, Vite, and Manifest V3.

## Build and install

```bash
npm install
npm run build:extension
```

The command verifies the generated extension at `dist/`. In Chrome, open `chrome://extensions`, enable **Developer mode**, select **Load unpacked**, and choose the `dist` folder. Do not select `src`, `public`, or the repository root.

To create a zip for transfer:

```bash
npm run package:extension
```

This creates `telegram-auto-bot-extension.zip`. For local development, `npm run dev` serves the UI as a web page; it does not install an extension into Chrome.

The Settings page controls the FastAPI URL; the bundle contains no AI or database secrets.
