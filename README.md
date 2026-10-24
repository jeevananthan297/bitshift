# SplitFlow — Full-stack Expense Splitter

SplitFlow is a local-first group expense app built with **Vue 3 + Vite**, **FastAPI**, and **SQLite**. It supports groups, members, four split methods, expense history, balance calculation, debt simplification, settlement records, analytics, budget tracking, CSV export, demo data, and a responsive dashboard.

> MVP note: this is a local hackathon demo without user authentication or real money transfer integration.

## Requirements
- Python 3.10+
- Node.js 20+ recommended
- npm

## Run on Windows (PowerShell)

### 1. Start the backend
Open Terminal 1:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000  
Interactive docs: http://127.0.0.1:8000/docs

### 2. Start the frontend
Open Terminal 2:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### macOS/Linux
Backend:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```
Frontend in a second terminal:
```bash
cd frontend
npm install
npm run dev
```

## Demo data
In the app, go to **My groups → Load demo**, or open `/docs`, select `POST /api/demo/seed`, and click **Try it out → Execute**. The seed endpoint only creates data when the database is empty.

## Tests
```bash
cd backend
pytest
```

## Core routes
- `GET /api/dashboard`
- `GET/POST /api/groups`
- `GET/POST /api/expenses`
- `PUT/DELETE /api/expenses/{id}`
- `GET /api/groups/{id}/balances`
- `GET /api/groups/{id}/settlement-plan`
- `POST /api/settlements`
- `GET /api/groups/{id}/analytics`
- `GET /api/expenses/export.csv`

## Data and limitations
- SQLite database is created automatically as `backend/splitflow.db` when starting the API from the backend directory.
- Money is stored in integer paise.
- The balance page uses a greedy debtor-creditor algorithm. It produces a valid settlement plan, though it does not guarantee the globally smallest possible transaction count for every balance configuration.
- Repayments are records only; no bank or payment provider is connected.
- This MVP has no authentication. Do not expose it publicly or use it for sensitive real-world financial records without adding authentication, authorization, and production hardening.
