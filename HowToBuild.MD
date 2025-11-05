# How to Build the Container (podman)

This builds a container image for the AccountSpy app using the provided `Containerfile`.

## Prerequisites
- Podman (or Docker) installed
- Internet access to fetch base images and Python wheels

## Build

```bash
# From the project root
podman build -t accountspy:latest -f Containerfile .
```

- `-t accountspy:latest`: names the image
- `-f Containerfile`: uses the included Containerfile

## What the image contains
- Python 3.13 slim base
- App installed dependencies from `requirements.txt`
- Application code from `backend/` and `frontend/`
- Entrypoint runs Uvicorn serving the FastAPI app defined at `backend/main.py`

## Notes
- The container expects environment variables at runtime: `ACCOUNTS_DIR`, `CURRENT_YEAR`.
- The container serves the static frontend from `frontend/` at the root `/` path.
- Example environment file format: see `.env.example`.
