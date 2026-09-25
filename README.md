# Telegram Automation Workspace

An independent, browser-operated workspace for researching groups, drafting posts, and controlling a posting queue. It does **not** use the Telegram API. The intended production bridge is a Chrome content script that reads the currently open Telegram Web page and performs user-authorized UI actions.

## Run locally

Requirements: Node 22 and Python 3.14.

```bash
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
npm run install:all
npm run dev
```

Open the Vite URL shown in the terminal. The UI falls back to seeded demo data if the API is unavailable, while the API persists data in `backend/automation.db`.

To load it in Chrome, run `npm run build`, open `chrome://extensions`, enable Developer mode, and load `extension-ui/dist` as an unpacked extension.

## Browser integration boundary

The API intentionally models actions rather than calling Telegram. A future Chrome content script should:

1. Report visible group/message metadata to `POST /api/groups/{id}/messages`.
2. Execute queued `post` or `delete` actions on Telegram Web after user confirmation.
3. Report replies and completion events back to the API.

This keeps credentials and Telegram session state in the browser and makes the local server safe to host online.