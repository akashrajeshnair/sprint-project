# from __future__ import annotations

# import re
# from datetime import datetime, timezone

# from fastapi import APIRouter, Depends, HTTPException, Query
# from pydantic import BaseModel, Field
# from sqlalchemy.orm import Session

# try:
#     from database import get_db
#     from models.messages import Message
#     from models.sessions import Session as ChatSession
#     from models.student_details import StudentProfile
#     from models.student_progress import StudentProgress
#     from models.users import User
#     from schemas.messages import MessageCreate, MessageRead
#     from schemas.sessions import SessionCreate, SessionRead, SessionUpdate
#     from services.rag import CONTENT_RETRIEVAL_TOOL, service as rag_service
# except ModuleNotFoundError:
#     from backend.database import get_db
#     from backend.models.messages import Message
#     from backend.models.sessions import Session as ChatSession
#     from backend.models.student_details import StudentProfile
#     from backend.models.student_progress import StudentProgress
#     from backend.models.users import User
#     from backend.schemas.messages import MessageCreate, MessageRead
#     from backend.schemas.sessions import SessionCreate, SessionRead, SessionUpdate
#     from backend.services.rag import CONTENT_RETRIEVAL_TOOL, service as rag_service

# router = APIRouter(prefix="/api", tags=["chat"])
# _CONTROL_CHAR_RE = re.compile(r"[\x00-\x1F\x7F]")


# class ChatToolAskRequest(BaseModel):
#     session_id: int
#     question: str = Field(min_length=1)
#     role: str = Field(default="student", pattern="^(student|teacher)$")
#     learner_level: str = Field(default="beginner")
#     response_mode: str = Field(default="step-by-step")
#     selected_file: str | None = None
#     use_rag_context: bool = True
#     top_k: int = Field(default=1, ge=1, le=8)
#     persist_messages: bool = True


# def _clean_text(value: str | None) -> str:
#     if value is None:
#         return ""

#     text = str(value)
#     text = text.replace("\\n", " ").replace("\\r", " ").replace("\\t", " ")
#     text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
#     text = _CONTROL_CHAR_RE.sub(" ", text)
#     return " ".join(text.split())


# def _clean_sources(sources: list[dict] | None) -> list[dict]:
#     cleaned: list[dict] = []
#     for item in sources or []:
#         if not isinstance(item, dict):
#             continue
#         cleaned.append(
#             {
#                 "source": _clean_text(item.get("source")),
#                 "page": item.get("page"),
#                 "snippet": _clean_text(item.get("snippet")),
#             }
#         )
#     return cleaned


# def _infer_subject(session_row: ChatSession, question: str, sources: list[dict]) -> str:
#     # 1. Prefer session subject if already stored
#     if session_row.subject and str(session_row.subject).strip():
#         return str(session_row.subject).strip()

#     q = (question or "").lower()

#     # 2. Very simple keyword-based inference
#     if any(word in q for word in ["dbms", "database", "sql", "table", "normalization"]):
#         return "DBMS"
#     if any(word in q for word in ["algebra", "equation", "quadratic", "mathematics", "math"]):
#         return "Mathematics"
#     if any(word in q for word in ["physics", "motion", "kinematics", "force"]):
#         return "Physics"
#     if any(word in q for word in ["chemistry", "atom", "periodic", "molecule"]):
#         return "Chemistry"
#     if any(word in q for word in ["history", "civilization", "medieval", "modern history"]):
#         return "History"
#     if any(word in q for word in ["biology", "cell", "organism", "genetics"]):
#         return "Biology"

#     # 3. Infer from retrieved source file names if useful
#     for item in sources or []:
#         source_name = str(item.get("source", "")).lower()
#         if "dbms" in source_name:
#             return "DBMS"
#         if "math" in source_name:
#             return "Mathematics"
#         if "physics" in source_name:
#             return "Physics"
#         if "chem" in source_name:
#             return "Chemistry"
#         if "history" in source_name:
#             return "History"
#         if "bio" in source_name:
#             return "Biology"

#     return "General"


# def _infer_topic(question: str) -> str:
#     text = _clean_text(question)
#     if not text:
#         return "General Topic"

#     # Keep topic readable and not too long
#     words = text.split()
#     topic = " ".join(words[:6]).strip()
#     return topic[:80] if topic else "General Topic"


# def _score_increment_from_answer(answer: str) -> float:
#     # Small engagement-based score gain per useful student chat
#     text = _clean_text(answer)
#     if not text:
#         return 0.02
#     length = len(text.split())

#     if length >= 120:
#         return 0.10
#     if length >= 60:
#         return 0.07
#     if length >= 20:
#         return 0.05
#     return 0.03


# def _ensure_student_profile(db: Session, user_id: int) -> StudentProfile:
#     profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
#     if profile:
#         return profile

#     profile = StudentProfile(
#         user_id=user_id,
#         grade_level="Unknown",
#         learning_style="theoretical",
#         subjects_enrolled=[],
#         xp_points=0,
#         last_active_at=datetime.now(timezone.utc),
#     )
#     db.add(profile)
#     db.commit()
#     db.refresh(profile)
#     return profile


# def _update_student_learning_tables(
#     db: Session,
#     session_row: ChatSession,
#     question: str,
#     cleaned_answer: str,
#     cleaned_sources: list[dict],
# ) -> None:
#     user = db.query(User).filter(User.user_id == session_row.user_id).first()
#     if not user or user.role != "student":
#         return

#     profile = _ensure_student_profile(db, user.user_id)

#     now = datetime.now(timezone.utc)
#     inferred_subject = _infer_subject(session_row, question, cleaned_sources)
#     inferred_topic = session_row.topic.strip() if session_row.topic else _infer_topic(question)

#     # Update session subject/topic if missing so future chats stay consistent
#     if not session_row.subject:
#         session_row.subject = inferred_subject
#     if not session_row.topic:
#         session_row.topic = inferred_topic

#     # Update student profile
#     xp_gain = 10
#     profile.xp_points = int(profile.xp_points or 0) + xp_gain
#     profile.last_active_at = now

#     # Keep subjects_enrolled updated
#     current_subjects = profile.subjects_enrolled or []
#     if inferred_subject and inferred_subject not in current_subjects:
#         current_subjects.append(inferred_subject)
#         profile.subjects_enrolled = current_subjects

#     # Upsert student_progress using the unique constraint:
#     # (student_profile_id, subject, topic)
#     progress_row = (
#         db.query(StudentProgress)
#         .filter(
#             StudentProgress.student_profile_id == profile.student_profile_id,
#             StudentProgress.subject == inferred_subject,
#             StudentProgress.topic == inferred_topic,
#         )
#         .first()
#     )

#     increment = _score_increment_from_answer(cleaned_answer)

#     if progress_row:
#         old_score = float(progress_row.score or 0)
#         progress_row.score = round(min(1.0, old_score + increment), 2)
#         progress_row.updated_at = now
#     else:
#         progress_row = StudentProgress(
#             student_profile_id=profile.student_profile_id,
#             subject=inferred_subject,
#             topic=inferred_topic,
#             score=round(min(1.0, 0.50 + increment), 2),
#             updated_at=now,
#         )
#         db.add(progress_row)

#     session_row.updated_at = now
#     db.commit()


# @router.post("/sessions", response_model=SessionRead)
# def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> SessionRead:
#     row = ChatSession(**payload.model_dump())
#     db.add(row)
#     db.commit()
#     db.refresh(row)
#     return row


# @router.get("/sessions", response_model=list[SessionRead])
# def list_sessions(
#     user_id: int | None = Query(default=None),
#     db: Session = Depends(get_db),
# ) -> list[SessionRead]:
#     query = db.query(ChatSession)
#     if user_id is not None:
#         query = query.filter(ChatSession.user_id == user_id)
#     return query.order_by(ChatSession.updated_at.desc(), ChatSession.session_id.desc()).all()


# @router.get("/sessions/{session_id}", response_model=SessionRead)
# def get_session(session_id: int, db: Session = Depends(get_db)) -> SessionRead:
#     row = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
#     if not row:
#         raise HTTPException(status_code=404, detail="Session not found")
#     return row


# @router.delete("/sessions/{session_id}")
# def delete_session(
#     session_id: int,
#     user_id: int | None = Query(default=None),
#     db: Session = Depends(get_db),
# ) -> dict:
#     query = db.query(ChatSession).filter(ChatSession.session_id == session_id)
#     if user_id is not None:
#         query = query.filter(ChatSession.user_id == user_id)

#     row = query.first()
#     if not row:
#         raise HTTPException(status_code=404, detail="Session not found")

#     db.delete(row)
#     db.commit()
#     return {
#         "ok": True,
#         "deleted_session_id": session_id,
#     }


# @router.patch("/sessions/{session_id}", response_model=SessionRead)
# def update_session(session_id: int, payload: SessionUpdate, db: Session = Depends(get_db)) -> SessionRead:
#     row = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
#     if not row:
#         raise HTTPException(status_code=404, detail="Session not found")

#     updates = payload.model_dump(exclude_unset=True)
#     for key, value in updates.items():
#         setattr(row, key, value)

#     db.commit()
#     db.refresh(row)
#     return row


# @router.post("/messages", response_model=MessageRead)
# def create_message(payload: MessageCreate, db: Session = Depends(get_db)) -> MessageRead:
#     session_row = db.query(ChatSession).filter(ChatSession.session_id == payload.session_id).first()
#     if not session_row:
#         raise HTTPException(status_code=404, detail="Session not found")

#     row = Message(**payload.model_dump())
#     db.add(row)
#     db.commit()
#     db.refresh(row)

#     session_row.updated_at = row.created_at
#     db.commit()

#     return row


# @router.get("/sessions/{session_id}/messages", response_model=list[MessageRead])
# def list_messages(session_id: int, db: Session = Depends(get_db)) -> list[MessageRead]:
#     session_row = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
#     if not session_row:
#         raise HTTPException(status_code=404, detail="Session not found")

#     return (
#         db.query(Message)
#         .filter(Message.session_id == session_id)
#         .order_by(Message.created_at.asc(), Message.message_id.asc())
#         .all()
#     )


# @router.post("/chat/ask")
# def chat_ask_with_rag_tool(payload: ChatToolAskRequest, db: Session = Depends(get_db)) -> dict:
#     session_row = db.query(ChatSession).filter(ChatSession.session_id == payload.session_id).first()
#     if not session_row:
#         raise HTTPException(status_code=404, detail="Session not found")

#     result = rag_service.answer_with_agent_loop(
#         question=payload.question,
#         role=payload.role,
#         learner_level=payload.learner_level,
#         response_mode=payload.response_mode,
#         selected_file=payload.selected_file,
#         use_rag_context=payload.use_rag_context,
#         top_k=payload.top_k,
#         max_steps=2,
#     )

#     cleaned_answer = _clean_text(result.get("answer"))
#     cleaned_sources = _clean_sources(result.get("sources"))

#     user_message_id: int | None = None
#     assistant_message_id: int | None = None

#     if payload.persist_messages:
#         user_row = Message(
#             session_id=payload.session_id,
#             role="user",
#             content=payload.question,
#         )
#         db.add(user_row)
#         db.commit()
#         db.refresh(user_row)
#         user_message_id = user_row.message_id

#         assistant_row = Message(
#             session_id=payload.session_id,
#             role="assistant",
#             content=cleaned_answer,
#             tool_calls_used=result.get("tool_calls_used") or [],
#         )
#         db.add(assistant_row)
#         db.commit()
#         db.refresh(assistant_row)
#         assistant_message_id = assistant_row.message_id

#         session_row.updated_at = assistant_row.created_at
#         db.commit()

#         # NEW: update student_profiles and student_progress after every student chat
#         _update_student_learning_tables(
#             db=db,
#             session_row=session_row,
#             question=payload.question,
#             cleaned_answer=cleaned_answer,
#             cleaned_sources=cleaned_sources,
#         )

#     return {
#         "answer": cleaned_answer,
#         "sources": cleaned_sources,
#         "tool_calls_used": result.get("tool_calls_used", []),
#         "context_used": bool(result.get("context_used", False)),
#         "messages": {
#             "user_message_id": user_message_id,
#             "assistant_message_id": assistant_message_id,
#         },
#     }

from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from database import get_db
    from models.messages import Message
    from models.sessions import Session as ChatSession
    from models.student_details import StudentProfile
    from models.student_progress import StudentProgress
    from models.users import User
    from schemas.messages import MessageCreate, MessageRead
    from schemas.sessions import SessionCreate, SessionRead, SessionUpdate
    from services.rag import CONTENT_RETRIEVAL_TOOL, service as rag_service
except ModuleNotFoundError:
    from backend.database import get_db
    from backend.models.messages import Message
    from backend.models.sessions import Session as ChatSession
    from backend.models.student_details import StudentProfile
    from backend.models.student_progress import StudentProgress
    from backend.models.users import User
    from backend.schemas.messages import MessageCreate, MessageRead
    from backend.schemas.sessions import SessionCreate, SessionRead, SessionUpdate
    from backend.services.rag import CONTENT_RETRIEVAL_TOOL, service as rag_service

router = APIRouter(prefix="/api", tags=["chat"])
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1F\x7F]")


class ChatToolAskRequest(BaseModel):
    user_id: int
    session_id: int | None = None
    question: str = Field(min_length=1)
    role: str = Field(default="student", pattern="^(student|teacher)$")
    learner_level: str = Field(default="beginner")
    response_mode: str = Field(default="step-by-step")
    selected_file: str | None = None
    use_rag_context: bool = True
    use_web_search: bool = False
    top_k: int = Field(default=1, ge=1, le=8)
    persist_messages: bool = True
    create_new_session: bool = True


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


def _infer_subject(question: str, sources: list[dict] | None = None) -> str:
    q = (question or "").lower()

    if any(word in q for word in ["dbms", "database", "sql", "normalization", "table", "schema"]):
        return "DBMS"
    if any(word in q for word in ["algebra", "equation", "quadratic", "mathematics", "math"]):
        return "Mathematics"
    if any(word in q for word in ["physics", "motion", "kinematics", "force", "velocity"]):
        return "Physics"
    if any(word in q for word in ["chemistry", "atom", "periodic", "molecule", "chemical"]):
        return "Chemistry"
    if any(word in q for word in ["history", "civilization", "medieval", "modern history"]):
        return "History"
    if any(word in q for word in ["biology", "cell", "organism", "genetics"]):
        return "Biology"

    for item in sources or []:
        source_name = str(item.get("source", "")).lower()
        if "dbms" in source_name:
            return "DBMS"
        if "math" in source_name:
            return "Mathematics"
        if "physics" in source_name:
            return "Physics"
        if "chem" in source_name:
            return "Chemistry"
        if "history" in source_name:
            return "History"
        if "bio" in source_name:
            return "Biology"

    return "General"


def _infer_topic(question: str) -> str:
    text = _clean_text(question)
    if not text:
        return "General Topic"

    removable_prefixes = [
        "what is",
        "explain",
        "define",
        "tell me about",
        "give me",
        "describe",
        "can you explain",
        "please explain",
    ]

    lowered = text.lower()
    for prefix in removable_prefixes:
        if lowered.startswith(prefix):
            text = text[len(prefix):].strip(" ?.-")
            break

    words = text.split()
    topic = " ".join(words[:6]).strip()
    return (topic or "General Topic").title()[:80]


def _score_increment_from_answer(answer: str) -> float:
    text = _clean_text(answer)
    if not text:
        return 0.02

    length = len(text.split())
    if length >= 120:
        return 0.10
    if length >= 60:
        return 0.07
    if length >= 20:
        return 0.05
    return 0.03


def _ensure_student_profile(db: Session, user_id: int) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if profile:
        return profile

    profile = StudentProfile(
        user_id=user_id,
        grade_level="Unknown",
        learning_style="theoretical",
        subjects_enrolled=[],
        xp_points=0,
        last_active_at=datetime.now(timezone.utc),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _update_student_learning_tables(
    db: Session,
    user_id: int,
    subject: str,
    topic: str,
    cleaned_answer: str,
) -> None:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role != "student":
        return

    profile = _ensure_student_profile(db, user.user_id)
    now = datetime.now(timezone.utc)

    profile.last_active_at = now
    profile.xp_points = int(profile.xp_points or 0) + 10

    current_subjects = profile.subjects_enrolled or []
    if subject and subject not in current_subjects:
        current_subjects.append(subject)
        profile.subjects_enrolled = current_subjects

    progress_row = (
        db.query(StudentProgress)
        .filter(
            StudentProgress.student_profile_id == profile.student_profile_id,
            StudentProgress.subject == subject,
            StudentProgress.topic == topic,
        )
        .first()
    )

    increment = _score_increment_from_answer(cleaned_answer)

    if progress_row:
        old_score = float(progress_row.score or 0)
        progress_row.score = round(min(1.0, old_score + increment), 2)
        progress_row.updated_at = now
    else:
        progress_row = StudentProgress(
            student_profile_id=profile.student_profile_id,
            subject=subject,
            topic=topic,
            score=round(min(1.0, 0.50 + increment), 2),
            updated_at=now,
        )
        db.add(progress_row)

    db.commit()


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
    return {"ok": True, "deleted_session_id": session_id}


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
    user = db.query(User).filter(User.user_id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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

    inferred_subject = _infer_subject(payload.question, cleaned_sources)
    inferred_topic = _infer_topic(payload.question)

    session_row = None
    if payload.session_id is not None and not payload.create_new_session:
        session_row = db.query(ChatSession).filter(ChatSession.session_id == payload.session_id).first()
        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found")

    if session_row is None:
        session_row = ChatSession(
            user_id=payload.user_id,
            subject=inferred_subject,
            topic=inferred_topic,
            difficulty_level=payload.learner_level,
        )
        db.add(session_row)
        db.commit()
        db.refresh(session_row)
    else:
        session_row.subject = inferred_subject
        session_row.topic = inferred_topic
        session_row.difficulty_level = payload.learner_level
        db.commit()
        db.refresh(session_row)

    user_message_id: int | None = None
    assistant_message_id: int | None = None

    if payload.persist_messages:
        user_row = Message(
            session_id=session_row.session_id,
            role="user",
            content=payload.question,
        )
        db.add(user_row)
        db.commit()
        db.refresh(user_row)
        user_message_id = user_row.message_id

        assistant_row = Message(
            session_id=session_row.session_id,
            role="assistant",
            content=cleaned_answer,
            tool_calls_used=result.get("tool_calls_used") or [],
        )
        db.add(assistant_row)
        db.commit()
        db.refresh(assistant_row)
        assistant_message_id = assistant_row.message_id

        session_row.updated_at = assistant_row.created_at
        db.commit()

        _update_student_learning_tables(
            db=db,
            user_id=payload.user_id,
            subject=inferred_subject,
            topic=inferred_topic,
            cleaned_answer=cleaned_answer,
        )

    return {
        "session_id": session_row.session_id,
        "subject": inferred_subject,
        "topic": inferred_topic,
        "answer": cleaned_answer,
        "sources": cleaned_sources,
        "tool_calls_used": result.get("tool_calls_used", []),
        "context_used": bool(result.get("context_used", False)),
        "messages": {
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id,
        },
    }