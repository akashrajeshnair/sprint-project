from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from database import get_db
    from models.messages import Message
    from models.sessions import Session as ChatSession
    from schemas.messages import MessageCreate, MessageRead
    from schemas.sessions import SessionCreate, SessionRead, SessionUpdate
    from services.rag import CONTENT_RETRIEVAL_TOOL, service as rag_service
except ModuleNotFoundError:
    from backend.database import get_db
    from backend.models.messages import Message
    from backend.models.sessions import Session as ChatSession
    from backend.schemas.messages import MessageCreate, MessageRead
    from backend.schemas.sessions import SessionCreate, SessionRead, SessionUpdate
    from backend.services.rag import CONTENT_RETRIEVAL_TOOL, service as rag_service

router = APIRouter(prefix="/api", tags=["chat"])
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1F\x7F]")


class ChatToolAskRequest(BaseModel):
    session_id: int
    question: str = Field(min_length=1)
    role: str = Field(default="student", pattern="^(student|teacher)$")
    learner_level: str = Field(default="beginner")
    response_mode: str = Field(default="step-by-step")
    selected_file: str | None = None
    use_rag_context: bool = True
    use_web_search: bool = False
    top_k: int = Field(default=1, ge=1, le=8)
    persist_messages: bool = True


def _clean_text(value: str | None) -> str:
    if value is None:
        return ""

    text = str(value)
    text = text.replace("\\n", " ").replace("\\r", " ").replace("\\t", " ")
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    text = _CONTROL_CHAR_RE.sub(" ", text)
    return " ".join(text.split())


def _clean_sources(sources: list[dict] | None) -> list[dict]:
    cleaned: list[dict] = []
    for item in sources or []:
        if not isinstance(item, dict):
            continue
        cleaned.append(
            {
                "source": _clean_text(item.get("source")),
                "page": item.get("page"),
                "snippet": _clean_text(item.get("snippet")),
            }
        )
    return cleaned


@router.post("/sessions", response_model=SessionRead)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> SessionRead:
    row = ChatSession(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/sessions", response_model=list[SessionRead])
def list_sessions(
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[SessionRead]:
    query = db.query(ChatSession)
    if user_id is not None:
        query = query.filter(ChatSession.user_id == user_id)
    return query.order_by(ChatSession.updated_at.desc(), ChatSession.session_id.desc()).all()


@router.get("/sessions/{session_id}", response_model=SessionRead)
def get_session(session_id: int, db: Session = Depends(get_db)) -> SessionRead:
    row = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    return row


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(ChatSession).filter(ChatSession.session_id == session_id)
    if user_id is not None:
        query = query.filter(ChatSession.user_id == user_id)

    row = query.first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(row)
    db.commit()
    return {
        "ok": True,
        "deleted_session_id": session_id,
    }


@router.patch("/sessions/{session_id}", response_model=SessionRead)
def update_session(session_id: int, payload: SessionUpdate, db: Session = Depends(get_db)) -> SessionRead:
    row = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(row, key, value)

    db.commit()
    db.refresh(row)
    return row


@router.post("/messages", response_model=MessageRead)
def create_message(payload: MessageCreate, db: Session = Depends(get_db)) -> MessageRead:
    session_row = db.query(ChatSession).filter(ChatSession.session_id == payload.session_id).first()
    if not session_row:
        raise HTTPException(status_code=404, detail="Session not found")

    row = Message(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)

    session_row.updated_at = row.created_at
    db.commit()

    return row


@router.get("/sessions/{session_id}/messages", response_model=list[MessageRead])
def list_messages(session_id: int, db: Session = Depends(get_db)) -> list[MessageRead]:
    session_row = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session_row:
        raise HTTPException(status_code=404, detail="Session not found")

    return (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc(), Message.message_id.asc())
        .all()
    )


@router.post("/chat/ask")
def chat_ask_with_rag_tool(payload: ChatToolAskRequest, db: Session = Depends(get_db)) -> dict:
    session_row = db.query(ChatSession).filter(ChatSession.session_id == payload.session_id).first()
    if not session_row:
        raise HTTPException(status_code=404, detail="Session not found")

    result = rag_service.answer_with_agent_loop(
        question=payload.question,
        role=payload.role,
        learner_level=payload.learner_level,
        response_mode=payload.response_mode,
        selected_file=payload.selected_file,
        use_rag_context=payload.use_rag_context,
        use_web_search=payload.use_web_search,
        top_k=payload.top_k,
        max_steps=2,
    )
    cleaned_answer = _clean_text(result.get("answer"))
    cleaned_sources = _clean_sources(result.get("sources"))

    user_message_id: int | None = None
    assistant_message_id: int | None = None

    if payload.persist_messages:
        user_row = Message(
            session_id=payload.session_id,
            role="user",
            content=payload.question,
        )
        db.add(user_row)
        db.commit()
        db.refresh(user_row)
        user_message_id = user_row.message_id

        assistant_row = Message(
            session_id=payload.session_id,
            role="assistant",
            content=cleaned_answer,
            tool_calls_used=result.get("tool_calls_used")
            or [],
        )
        db.add(assistant_row)
        db.commit()
        db.refresh(assistant_row)
        assistant_message_id = assistant_row.message_id

        session_row.updated_at = assistant_row.created_at
        db.commit()

    return {
        "answer": cleaned_answer,
        "sources": cleaned_sources,
        "tool_calls_used": result.get("tool_calls_used", []),
        "context_used": bool(result.get("context_used", False)),
        "messages": {
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id,
        },
    }
