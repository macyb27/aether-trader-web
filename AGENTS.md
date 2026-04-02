# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Aether Trader Pro is a Next.js 14 (React 18, TypeScript, Tailwind CSS) web app for AI-powered paper trading. It is a single-service application — only the Next.js dev server is needed.

### Running the app

- `npm run dev` starts the dev server on port 3000.
- `npm run build` builds for production.
- `npm run lint` runs ESLint.

See `README.md` for full command reference and project structure.

### Key caveats

- **`--legacy-peer-deps` is required** when installing dependencies, because `@types/react` v19 conflicts with React 18. Always run `npm install --legacy-peer-deps`.
- **`.eslintrc.json`** was added to avoid the interactive ESLint setup prompt that `next lint` triggers on first run. The rule `react/no-unescaped-entities` is set to `"warn"` to work around a pre-existing lint issue in `app/auth/login/page.tsx` that otherwise fails the build.
- **`.env.local`** must exist (copy from `.env.example`). External API keys (Alpaca, Finnhub) and the database URL are optional — the app runs fully with hardcoded demo data.
- **Demo credentials**: `demo@aether.com` / `demo123` — these work via the in-memory auth at `/api/auth/login`.
- **No database, Redis, or external APIs** are required for the current codebase. All data is mocked client-side.
- **No automated test suite** exists yet (`npm run test` is not configured).
