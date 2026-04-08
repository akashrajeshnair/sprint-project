# sprint-project

# LLM Tokens Tracker

Simple project with:

- FastAPI backend
- Streamlit frontend
- PostgreSQL database

Database details:

- database: capgemini_sprint
- table: models
- columns: id, model_name, total_tokens, tokens_used

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Environment

Use `.env` (or `.env.example`) with:

```env
DATABASE_URL=postgresql+psycopg2://postgres:admin@localhost:5432/capgemini_sprint
API_BASE_URL=http://127.0.0.1:8000
```

## Run

Start backend:

```bash
python -m uvicorn backend.main:app --reload
```

Start Streamlit in another terminal:

```bash
python -m streamlit run streamlit_app.py
```

## API

- GET `/llms` : list all models
- POST `/llms` : add a model

## Dump Database

```bash
pg_dump -p 5432 -d capgemini_sprint --no-owner --no-acl --clean --if-exists --schema-only -f database/schema.sql
```