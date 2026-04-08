from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rag_service import DATA_DIR, UPLOAD_DIR, BASE_DIR, service

STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

app = FastAPI(title="Smart Education RAG Assistant", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    role: str = Field(default="student", pattern="^(student|teacher)$")
    learner_level: str = Field(default="beginner")
    response_mode: str = Field(default="step-by-step")
    selected_file: str | None = Field(default=None)
    use_rag_context: bool = Field(default=True)
    top_k: int = Field(default=4, ge=1, le=8)


@app.on_event("startup")
def startup_event() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    service.prepare()


@app.get("/")
def home() -> FileResponse:
    return FileResponse(INDEX_FILE)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/index/status")
def index_status() -> dict:
    files = service.list_indexed_files()
    return {
        "indexed_files": files,
        "indexed_file_count": len(files),
        "indexed_chunks": sum(int(item.get("chunks", 0)) for item in files),
    }


@app.post("/api/index/sync")
def sync_index() -> dict:
    result = service.sync_uploads_incremental()
    return {
        "processed": result["processed"],
        "skipped": result["skipped"],
        "failed": result["failed"],
        "indexed_files": result["indexed_files"],
    }


@app.get("/api/files")
def list_files() -> dict:
    return {"files": service.list_indexed_files()}


@app.post("/api/index/rebuild")
def rebuild_index() -> dict:
    count = service.build_index()
    return {"indexed_chunks": count}


@app.post("/api/upload")
async def upload_documents(files: list[UploadFile] = File(...)) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    saved_paths: list[Path] = []
    allowed_suffixes = {".pdf", ".txt", ".md", ".markdown"}

    try:
        for uploaded_file in files:
            if not uploaded_file.filename:
                raise HTTPException(status_code=400, detail="One of the uploaded files has no filename.")

            safe_name = Path(uploaded_file.filename).name
            suffix = Path(safe_name).suffix.lower()
            if suffix not in allowed_suffixes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type for {safe_name}. Allowed: PDF, TXT, MD.",
                )

            target_path = UPLOAD_DIR / safe_name
            target_path.write_bytes(await uploaded_file.read())
            saved_paths.append(target_path)

        chunk_count = service.ingest_files(saved_paths)
        return {
            "saved_files": [path.name for path in saved_paths],
            "indexed_chunks": chunk_count,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload/indexing failed: {exc}") from exc


@app.post("/api/ask")
def ask_question(payload: AskRequest) -> JSONResponse:
    result = service.answer_question(
        question=payload.question,
        role=payload.role,
        learner_level=payload.learner_level,
        response_mode=payload.response_mode,
        selected_file=payload.selected_file,
        use_rag_context=payload.use_rag_context,
        top_k=payload.top_k,
    )
    return JSONResponse(result)
