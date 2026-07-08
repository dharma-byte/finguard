# frontend

React analyst dashboard: live flagged transaction feed and a chat-style
investigation panel with cited sources.

## Run

Requires the backend running on `http://localhost:8000` (see `../backend/README.md`).

```
npm install
npm run dev
```

Vite proxies `/api/*` to the backend (see `vite.config.ts`).
