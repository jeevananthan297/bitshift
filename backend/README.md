# SplitFlow backend

## Windows PowerShell
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend: http://127.0.0.1:8000  
API docs: http://127.0.0.1:8000/docs

Seed demo data by calling `POST http://127.0.0.1:8000/api/demo/seed` (use Swagger `/docs`).
Run tests from `backend`: `pytest`
