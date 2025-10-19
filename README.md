# accountspy

## Run locally

- **Prerequisites**: Python 3.9+

### 1) Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Start the server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000 in your browser.

## Project structure

- `backend/main.py` FastAPI app that loads CSV into an in-memory DB and serves the frontend.
- `frontend/index.html` Static React app (via CDN) consuming the API.
- `requirements.txt` Python dependencies.
- `.env.example` Example env config.

## API

- `GET /api/properties` List all properties.
- `GET /api/properties/{property}` Get a single property by id.
- `POST /api/properties` Create a new property (JSON body per fields in CSV).
- `DELETE /api/properties/{property}` Delete property by id.
- `GET /api/companies` List of company names derived from `companies.csv`.
- `GET /api/company-records` List full company records from `companies.csv`.
- `POST /api/company-records` Create a company record.
- `DELETE /api/company-records/{companyname}` Delete a company record.

Notes:

- Data is in-memory only and resets on server restart.
- On startup, data is loaded from CSV files located in `ENTITIES_DIR` if present.

## Environment configuration

- Copy `.env.example` to `.env` in the project root and edit:

```
# Directory containing your CSV entities
ENTITIES_DIR=/absolute/path/to/entities
```

- Place these CSVs in `ENTITIES_DIR`:
  - `properties.csv` with header `#property,cost,landValue,renovation,loanClosingCOst,ownerCount,purchaseDate,propMgmgtComp`
  - `companies.csv` with header `#companyname,rentPercentage`

## Data rules

- Company names are normalized to lowercase and must be alphanumeric (no spaces). Rows violating this are ignored.
- The property field `propMgmgtComp` must match a company from `companies.csv` (lowercase, alphanumeric) or the POST will be rejected.
- The UI dropdown for `propMgmgtComp` is built from `GET /api/companies` which derives from `companies.csv`.