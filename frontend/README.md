# frontend/README.md
# SoulSmith Frontend

The SoulSmith frontend is a React, TypeScript, Vite, Tailwind, and Three.js application that presents the dice sanctuary, narrative encounter flow, Soul sheet, Chronicle, phenomena, and mythic gallery experiences.

## Requirements

- Node.js 22, matching the GitHub Actions workflow.
- npm, using the committed `package-lock.json` for reproducible installs.

## Local setup

```bash
cd frontend
npm ci
npm run dev
```

The development server is provided by Vite. Configure API endpoints through `.env` values copied from `.env.example`; do not commit local secrets or machine-specific URLs.

## Quality gates

Run these commands before pushing frontend changes:

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

`npm run test` executes `scripts/run-tests.mjs`, which validates the frontend side of the canonical numeric dice roll contract. `npm run build` performs a TypeScript project build before creating the production Vite bundle.

## CI parity

The `Frontend CI` GitHub Actions workflow runs the same install, lint, typecheck, test, and build commands from this directory. A Vite large-chunk advisory is acceptable unless the command exits with a non-zero status.
