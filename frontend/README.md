# Frontend (React) – Nirman

A modern React frontend for building and previewing AI‑generated web apps.

## Quick Start

- Install: `npm install`
- Dev server: `npm start`
- Build: `npm run build`

The app runs at http://localhost:3000 and connects to the backend API configured in `src/lib/api.js`.

## Features

- Chat‑driven builder with live preview
- Tailwind‑styled UI components
- Provider selection (OpenAI/Gemini/Claude)

## Configuration

- API endpoints are defined in `src/lib/api.js`.
- Update environment variables via `.env` (e.g., `REACT_APP_API_BASE`).

## Scripts

- `npm start`: Start dev server.
- `npm run build`: Production build to `build/`.

## Notes

- Visual‑edit/emergent assets were removed to keep the frontend self‑contained.
