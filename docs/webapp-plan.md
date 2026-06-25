# Web App Plan

The desktop app is the first target, but the conversion logic is kept under `core/` so it can be reused by a CLI or web server.

## Web App Version Direction

### Phase 1: Local Web App

- FastAPI + HTML or Streamlit.
- Runs on the user's PC at `localhost`.
- Files are not sent to an external server.
- Calls the same converter used by the desktop GUI.

### Phase 2: Hosted Website

- Users upload PDFs from the browser.
- The server converts files and returns a zip download.
- Clear privacy guidance is required.
- Temporary upload cleanup must be automatic.

### Phase 3: SaaS

- User accounts.
- Conversion history.
- Large file processing.
- Paid plans.
- External API and server costs must be considered before this stage.

## Recommended Stack

- Backend: FastAPI.
- Frontend MVP: Jinja2 or Streamlit.
- Advanced frontend: Next.js.
- Job queue: Celery or RQ.
- Storage: local file system first, then S3-compatible storage.
- Deployment: Docker.
