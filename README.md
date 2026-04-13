# Sprint Project

This project has:

- FastAPI backend in `backend/`
- Streamlit frontend in `streamlit_app.py` and `pages/`

## 1) Prerequisites

- Windows PowerShell
- Python 3.13+
- PostgreSQL running locally

## 2) Setup

From project root:

```powershell
cd c:\Users\Kirtan\Desktop\sprint-project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 3) Environment variables

Create/update `.env` in project root.

Minimum required values:

```env
DATABASE_URL=postgresql+psycopg2://postgres:admin@localhost:5432/postgres
API_BASE_URL=http://127.0.0.1:8000
GROQ_API_KEY=your_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

Optional model settings:

```env
GROQ_MODEL=llama-3.1-8b-instant
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## 4) Run backend (FastAPI)

Open Terminal 1:

```powershell
cd c:\Users\Kirtan\Desktop\sprint-project\backend
c:/Users/Kirtan/Desktop/sprint-project/.venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Check server:

- http://127.0.0.1:8000/docs

## 5) Run frontend (Streamlit)

Open Terminal 2:

```powershell
cd c:\Users\Kirtan\Desktop\sprint-project
c:/Users/Kirtan/Desktop/sprint-project/.venv/Scripts/python.exe -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

Open:

- http://127.0.0.1:8501

## 6) Daily restart flow

1. Stop both terminals (`Ctrl+C`).
2. Start backend first.
3. Start frontend.
4. Refresh browser.

## 7) Common issues

### `ModuleNotFoundError: No module named 'jose'`

You are likely running global Python instead of project venv.

Use:

```powershell
c:/Users/Kirtan/Desktop/sprint-project/.venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### `FastAPI server is not running` on login

- Confirm backend is up at `http://127.0.0.1:8000/docs`
- Ensure `.env` has `API_BASE_URL=http://127.0.0.1:8000`
- Restart Streamlit after backend changes.

### `WinError 10013` when binding `0.0.0.0`

Run backend with host `127.0.0.1` instead.

### RAG answers look stale after code update

- Restart backend (`--reload` usually handles code changes)
- If changing `.env`, always restart backend and frontend.

## Dump Database

```bash
pg_dump -p 5432 -d capgemini_sprint --no-owner --no-acl --clean --if-exists --schema-only -f database/schema.sql
```