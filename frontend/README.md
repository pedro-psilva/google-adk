# Frontend

Minimal frontend for the profile-report platform, built as a separate application from the backend.

## Stack

- React + TypeScript + Vite
- Atomic Design component organization
- Relative HTTP contracts ready for same-origin deploys or Vite proxy in local development

## Commands

- `npm.cmd install`
- `npm.cmd run dev`
- `npm.cmd run build`

## Environment

Copy `.env.example` to `.env` when needed.

- `VITE_API_BASE_URL`: optional absolute backend origin
- `VITE_DEV_BACKEND_ORIGIN`: used by the Vite dev proxy, defaults to `http://127.0.0.1:8000`

## Notes

- The frontend stays separate from the backend and only consumes HTTP contracts.
- Google OAuth currently opens in a popup and the user can refresh the connection state after consent.
- The backend still needs CORS/session hardening if this frontend is served from a different origin in production.
