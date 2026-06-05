# Korean PII Guardrail Web Console

React/Vite product console for the local FastAPI service.

```powershell
cd korean_pii_guardrail_v0_2\web
npm install
npm run dev
```

Default dev URL: `http://127.0.0.1:5173`

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`. Use `VITE_API_BASE_URL` only when the API runs elsewhere.
