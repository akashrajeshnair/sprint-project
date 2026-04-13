# from __future__ import annotations

# import os
# from contextlib import asynccontextmanager
# from pathlib import Path

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# import uvicorn
# =======
# # from fastapi import FastAPI
# # from backend.routes.auth import router as auth_router

# # app = FastAPI()

# # app.include_router(auth_router, prefix="/auth", tags=["Auth"])

# # from backend.routes.users import router as users_router

# # app.include_router(users_router, tags=["Users"])
# print("🚀 MAIN FILE RUNNING")
# from fastapi import FastAPI
# from backend.routes.auth import router as auth_router
# from backend.routes.users import router as users_router   # ✅ MOVE UP

# STATIC_DIR = Path(__file__).resolve().parent / "static"

# try:
# 	# Works when running from `backend/` (e.g., `python main.py`)
# 	from services.rag import service as rag_service
# 	from models import messages as _messages_model  # noqa: F401
# 	from models import sessions as _sessions_model  # noqa: F401
# 	from models import users as _users_model  # noqa: F401
# 	from routes.chat import router as chat_router
# 	from routes.auth import router as auth_router
# except ModuleNotFoundError as exc:
# 	if exc.name not in {"routes", "models", "database", "schemas", "services"}:
# 		raise
# 	# Works when importing as package from project root
# 	from backend.services.rag import service as rag_service
# 	from backend.models import messages as _messages_model  # noqa: F401
# 	from backend.models import sessions as _sessions_model  # noqa: F401
# 	from backend.models import users as _users_model  # noqa: F401
# 	from backend.routes.chat import router as chat_router
# 	from backend.routes.auth import router as auth_router


# @asynccontextmanager
# async def lifespan(_: FastAPI):
# 	STATIC_DIR.mkdir(parents=True, exist_ok=True)
# 	backend_dir = Path(__file__).resolve().parent
# 	(backend_dir / "data").mkdir(parents=True, exist_ok=True)
# 	rag_service.sync_documents_incremental()
# 	yield


# app = FastAPI(title="Smart Education RAG Assistant", version="1.0.0", lifespan=lifespan)

# app.add_middleware(
# 	CORSMiddleware,
# 	allow_origins=["*"],
# 	allow_credentials=True,
# 	allow_methods=["*"],
# 	allow_headers=["*"],
# )

# app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
# app.include_router(auth_router, prefix="/auth", tags=["Auth"])
# app.include_router(chat_router)


# if __name__ == "__main__":
# 	host = os.getenv("HOST", "0.0.0.0")
# 	port = int(os.getenv("PORT", "8000"))
# 	reload_enabled = os.getenv("RELOAD", "true").lower() in {"1", "true", "yes", "on"}
# 	uvicorn.run("main:app", host=host, port=port, reload=reload_enabled)
# =======
# app.include_router(auth_router, prefix="/auth", tags=["Auth"])
# app.include_router(users_router, tags=["Users"])

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

STATIC_DIR = Path(__file__).resolve().parent / "static"

try:
    from services.rag import service as rag_service
    from models import messages as _messages_model  # noqa: F401
    from models import sessions as _sessions_model  # noqa: F401
    from models import users as _users_model  # noqa: F401
    from routes.chat import router as chat_router
    from routes.auth import router as auth_router
    from routes.users import router as users_router
except ModuleNotFoundError as exc:
    if exc.name not in {"routes", "models", "database", "schemas", "services"}:
        raise
    from backend.services.rag import service as rag_service
    from backend.models import messages as _messages_model  # noqa: F401
    from backend.models import sessions as _sessions_model  # noqa: F401
    from backend.models import users as _users_model  # noqa: F401
    from backend.routes.chat import router as chat_router
    from backend.routes.auth import router as auth_router
    from backend.routes.users import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    backend_dir = Path(__file__).resolve().parent
    (backend_dir / "data").mkdir(parents=True, exist_ok=True)
    rag_service.sync_documents_incremental()
    yield


app = FastAPI(
    title="Smart Education RAG Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router, tags=["Users"])
app.include_router(chat_router)


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_enabled = os.getenv("RELOAD", "true").lower() in {"1", "true", "yes", "on"}
    uvicorn.run("main:app", host=host, port=port, reload=reload_enabled)