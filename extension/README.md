# Telegram Auto Bot — Chrome Extension

React + TypeScript + Vite (Manifest V3, side panel).

Requires **Node.js 22+**.

```bash
cd extension
npm install
npm run dev    # development build with HMR
npm run build  # load extension/dist in chrome://extensions
```

Configure backend URL in **Settings** (default `http://localhost:8000`).

The only Telegram Web content script is injected into `https://web.telegram.org/*` and shows a manual Add/Skip group prompt. It does not read message content or automate Telegram controls. Real-group analysis accepts only message text that the user copies and imports into the side panel. Sending and deleting Telegram posts remain user actions.
