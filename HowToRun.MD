# How to Run AccountSpy on macOS

## 1) Install PyCharm (Community Edition)
- Open https://www.jetbrains.com/pycharm/download
- Download "Community" for macOS (Apple Silicon or Intel as appropriate)
- Open the .dmg and drag PyCharm to Applications
- Launch PyCharm and complete initial setup (default settings are fine)

## 2) Install Python 3
- Check if Python 3 exists:
```bash
python3 --version
```
- If missing or too old, install via Homebrew:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python
```
- Verify:
```bash
python3 --version
```

## 3) Open this project in PyCharm
- Launch PyCharm → "Open" → select the folder: `accountspy/`
- When prompted to create a virtual environment, accept it (recommended)

## 4) Create/activate a virtual environment (optional but recommended)
If PyCharm didn’t auto-create one, you can create it manually in Terminal:
```bash
cd /path/to/accountspy
python3 -m venv .venv
source .venv/bin/activate  # zsh/bash on macOS
```

## 5) Install dependencies
- Ensure your virtual environment is active (shows `(.venv)` in your shell)
- Install from `requirements.txt`:
```bash
pip install -r requirements.txt
```

## 6) Configure environment variables (.env)
Create a file named `.env` in the project root `accountspy/.env` with the following keys:
```env
ENTITIES_DIR=/absolute/path/to/entities/root
CURRENT_YEAR=2024
ACCOUNTS_DIR=/absolute/path/to/accounts/root
```
Notes:
- Use absolute paths.
- Example (yours will differ):
```env
ENTITIES_DIR=/Users/you/selfmanaged/cpa
CURRENT_YEAR=2024
ACCOUNTS_DIR=/Users/you/selfmanaged/cpa
```

## 7) Run the backend (FastAPI)
From Terminal in the project root:
```bash
python3 backend/main.py
```
You should see logs ending with:
```
Uvicorn running on http://127.0.0.1:8000
```

## 8) Use the app
- Open a browser to: http://127.0.0.1:8000
- The UI (`frontend/index.html`) is served by the backend

## 9) Common operations
- Reinstall deps after pull/update:
```bash
pip install -r requirements.txt
```
- Regenerate normalized/processed data and summaries: restart the backend

## 10) Troubleshooting
- If imports fail, ensure you installed from `requirements.txt` inside the active venv
- If you don’t see expected data, verify your `.env` paths and `CURRENT_YEAR`
- Check logs printed by `python3 backend/main.py` for hints


# Run with Podman (Container)

This section explains how to run the app using the container built from `Containerfile`.

## Prerequisites
- Image built as per `HowToBuild.MD`, e.g. `accountspy:latest`
- Podman installed (rootless recommended)

## Required environment
- `ACCOUNTS_DIR`: absolute path inside the container that points to your accounts root
- `CURRENT_YEAR`: processing year (e.g., `2024`)

Recommended approach: map your host accounts directory into the container at `/data` and set `ACCOUNTS_DIR=/data`.

## Example run (rootless)

```bash
# Replace these paths/values with your own
HOST_ACCOUNTS_DIR=/Users/you/selfmanaged/cpa
YEAR=2024

podman run --rm \
  -p 8000:8000 \
  -e ACCOUNTS_DIR=/data \
  -e CURRENT_YEAR=${YEAR} \
  -v "${HOST_ACCOUNTS_DIR}:/data:Z" \
  --name accountspy \
  accountspy:latest
```

- Access the UI at: http://127.0.0.1:8000
- The backend logs appear in the container output.

## Detached mode

```bash
podman run -d \
  -p 8000:8000 \
  -e ACCOUNTS_DIR=/data \
  -e CURRENT_YEAR=2024 \
  -v "/absolute/host/accounts:/data:Z" \
  --name accountspy \
  accountspy:latest

# View logs
podman logs -f accountspy

# Stop
podman stop accountspy
```

## Using an env file (optional)

Create `container.env`:

```env
ACCOUNTS_DIR=/data
CURRENT_YEAR=2024
```

Run with env file:

```bash
podman run --rm \
  --env-file ./container.env \
  -v "/absolute/host/accounts:/data:Z" \
  -p 8000:8000 \
  --name accountspy \
  accountspy:latest
```

## SELinux note (Linux hosts)

If your host uses SELinux, keep the `:Z` flag on `-v` so Podman relabels the volume for the container.
