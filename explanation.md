# Smart Education RAG Assistant

A **Streamlit** multi-page UI + a **FastAPI** backend that provides:

- Chatbot (RAG over PDFs + optional web search)
- Student progress tracking (XP + per-topic scores)
- Teacher visibility into student progress
- Admin user management

---

## Table of contents

- [1. Roles and pages](#1-roles-and-pages)
- [2. Architecture (high level)](#2-architecture-high-level)
- [3. Backend API (inputs/outputs)](#3-backend-api-inputsoutputs)
  - [3.1 Login](#31-login)
  - [3.2 Chat ask (main chatbot endpoint)](#32-chat-ask-main-chatbot-endpoint)
  - [3.3 Sessions and messages](#33-sessions-and-messages)
  - [3.4 Users and profiles](#34-users-and-profiles)
- [4. Tools (how they work)](#4-tools-how-they-work)
  - [4.1 `content_retrieval` (PDF RAG)](#41-content_retrieval-pdf-rag)
  - [4.2 `duckduckgo_search` (web search)](#42-duckduckgo_search-web-search)
  - [4.3 `user_score_lookup` (student scores)](#43-user_score_lookup-student-scores)
  - [4.4 `detailed_explanation` (long explanation)](#44-detailed_explanation-long-explanation)
- [5. Streamlit chatbot behavior](#5-streamlit-chatbot-behavior)
- [6. How progress tracking works](#6-how-progress-tracking-works)
- [7. Documents and indexing (RAG)](#7-documents-and-indexing-rag)
- [8. Configuration notes](#8-configuration-notes)
- [9. Tests](#9-tests)

---

## 1) Roles and pages

### Roles

- **Student**: chat + view profile/progress.
- **Teacher**: chat + view students and their progress.
- **Admin**: manage users.

### Pages (UI entry points)

Login:

- [streamlit_app.py](streamlit_app.py)

Student:

- Dashboard: [pages/student_dashboard.py](pages/student_dashboard.py)
- Profile + graphs: [pages/student_profile.py](pages/student_profile.py)
- Chatbot: [pages/chatbot.py](pages/chatbot.py)
- Leaderboard (calls `/students/leaderboard`, which is **not implemented** in current backend routes): [pages/leaderboard.py](pages/leaderboard.py)

Teacher:

- Dashboard: [pages/teacher_dashboard.py](pages/teacher_dashboard.py)
- Profile: [pages/teacher_profile.py](pages/teacher_profile.py)
- Student list (open a student): [pages/teacher_student_progress.py](pages/teacher_student_progress.py)
- Student profile (teacher view): [pages/teacher_student_profile.py](pages/teacher_student_profile.py)
- Chatbot: [pages/chatbot.py](pages/chatbot.py)

Admin:

- Dashboard: [pages/admin_dashboard.py](pages/admin_dashboard.py)
- View students: [pages/admin_view_students.py](pages/admin_view_students.py)
- View teachers: [pages/admin_view_teachers.py](pages/admin_view_teachers.py)
- Add user: [pages/admin_add_user.py](pages/admin_add_user.py)
- Manage users: [pages/admin_manage_users.py](pages/admin_manage_users.py)

---

## 2) Architecture (high level)

Frontend (Streamlit)

- Logs in via `POST /auth/login`.
- Stores `access_token`, `role`, `user_id` in `st.session_state`.
- The chatbot client attaches `Authorization: Bearer <token>` when `access_token` is present.

Backend (FastAPI)

- App entrypoint: [backend/main.py](backend/main.py)
- Routers:
  - Auth: [backend/routes/auth.py](backend/routes/auth.py)
  - Users/profiles: [backend/routes/users.py](backend/routes/users.py)
  - Chat + sessions/messages: [backend/routes/chat.py](backend/routes/chat.py)
- RAG + tools logic: [backend/services/rag.py](backend/services/rag.py)

Database

- SQLAlchemy models live in [backend/models/](backend/models/).
- Sessions/messages are persisted; student XP and topic scores are updated after chats.

---

## 3) Backend API (inputs/outputs)

### 3.1 Login

**Endpoint**: `POST /auth/login`

**Request**

```json
{
  "email": "student@example.com",
  "password": "..."
}
```

**Response**

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "role": "student",
  "user_id": 123
}
```

### 3.2 Chat ask (main chatbot endpoint)

**Endpoint**: `POST /api/chat/ask`

Used by the Streamlit chatbot page.

**Request** (see `ChatToolAskRequest` in [backend/routes/chat.py](backend/routes/chat.py))

```json
{
  "user_id": 123,
  "session_id": null,
  "question": "Explain normalization in DBMS",
  "role": "student",
  "learner_level": "beginner",
  "response_mode": "step-by-step",
  "selected_file": null,
  "use_rag_context": true,
  "use_web_search": false,
  "use_score_tool": true,
  "use_explanation_tool": true,
  "top_k": 3,
  "persist_messages": true,
  "create_new_session": true
}
```

**Response**

```json
{
  "session_id": 456,
  "subject": "DBMS",
  "topic": "Normalization In Dbms",
  "answer": "...",
  "sources": [{ "source": "dbms_notes.pdf", "page": 2, "snippet": "..." }],
  "tool_calls_used": [
    {
      "name": "content_retrieval",
      "arguments": {
        "question": "...",
        "role": "student",
        "selected_file": null,
        "top_k": 3
      },
      "result_count": 3,
      "step": 1
    }
  ],
  "context_used": true,
  "messages": { "user_message_id": 1001, "assistant_message_id": 1002 }
}
```

**Notes**

- If `create_new_session=true`, the backend creates a new `sessions` row and returns the new `session_id`.
- `subject` and `topic` are inferred from keywords and/or retrieved sources.

### 3.3 Sessions and messages

Used to list and reload past chats.

- `GET /api/sessions?user_id=<id>` → list sessions for a user
- `GET /api/sessions/{session_id}/messages` → list messages in a session
- `DELETE /api/sessions/{session_id}?user_id=<id>` → delete session (optionally scoped to user)

### 3.4 Users and profiles

Used by student/teacher/admin pages.

General:

- `GET /students` → list students
- `GET /teachers` → list teachers
- `GET /users` → list all users (admin)
- `POST /users` → create user
- `PUT /users/{user_id}` → update user
- `DELETE /users/{user_id}` → delete user (admins cannot be deleted)

Student-specific:

- `GET /student-profile/{user_id}` → full student profile + progress rows
- `GET /users/by-id/{user_id}` → user details (and student-profile fields if available)

---

## 4) Tools (how they work)

Tool implementations + routing live in [backend/services/rag.py](backend/services/rag.py).

The backend records tool usage in the `/api/chat/ask` response under `tool_calls_used`.

### 4.1 `content_retrieval` (PDF RAG)

**Purpose**: retrieve relevant text chunks from role-scoped PDFs.

**Inputs** (`ContentRetrievalInput`)

- `question` (required)
- `role` (`student|teacher`)
- `top_k` (1..8)
- `selected_file` (optional: restrict retrieval to a specific PDF filename)

**Outputs**

- Backend uses a list of `Document` chunks.
- API returns `sources[]` items of the form:
  - `source`: PDF filename
  - `page`: page number (if present)
  - `snippet`: first ~220 characters

**Indexing & storage**

- PDFs live under:
  - `backend/documents/students/`
  - `backend/documents/teachers/`
- On backend startup, `rag_service.sync_documents_incremental()` runs (see [backend/main.py](backend/main.py)).
- Each role builds a separate Chroma collection under `backend/chroma_db/<role_collection>`.
- Embeddings use `sentence-transformers/all-MiniLM-L6-v2` and are cached under `backend/.cache/huggingface/`.

**Chunking rules**

- Default: `RecursiveCharacterTextSplitter` (chunk size 900, overlap 150).
- Special case: PDFs whose filename starts with `comparison...` use numbered-section chunking.

### 4.2 `duckduckgo_search` (web search)

**Purpose**: fetch web snippets from DuckDuckGo when enabled.

**Inputs** (`WebSearchInput`)

- `question` (required)
- `max_results` (1..8)

**Outputs**

- Normalized `{title, snippet, url}` results.
- API converts them to `sources[]` where:
  - `source`: URL (or title)
  - `page`: `null`
  - `snippet`: first ~220 characters

**When it runs**

- If `use_rag_context=false` and `use_web_search=true`: web snippets are used to answer first.
- If `use_rag_context=true`, retrieval finds no chunks, and `use_web_search=true`: web search becomes a fallback.

### 4.3 `user_score_lookup` (student scores)

**Purpose**: return a student’s XP + topic-level scores.

**Inputs** (`UserScoreInput`)

- `user_id` (required)
- `subject` (optional)
- `topic` (optional)

**Output**

- A formatted score summary string.

**Access control**

- Effective only for users whose role is `student` (enforced in the chat route).

### 4.4 `detailed_explanation` (long explanation)

**Purpose**: generate a longer, structured explanation.

**Inputs** (`ExplanationInput`)

- `question` (required)
- `role` (`student|teacher`)
- `learner_level` (`beginner|intermediate|advanced`)

**Output**

- A numbered, multi-section explanation.
- If no LLM key is configured, the service returns a deterministic fallback.

**Trigger logic**
If `use_explanation_tool=true` and the prompt contains markers like `explain`, `in detail`, `deep dive`, `why`, `how does`, etc., the backend routes to this tool first.

---

## 5) Streamlit chatbot behavior

Implemented in [pages/chatbot.py](pages/chatbot.py).

### Session behavior

- Each submitted message is sent with `session_id=null` and `create_new_session=true`.
- That means the backend creates a **new chat session per submission**.
- Past sessions can still be loaded from the sidebar.

### Sidebar settings

Teacher sees:

- `use_rag_context`, `use_web_search`, `use_explanation_tool`
- `top_k` slider (1..8)
- `response_mode` (`step-by-step` or `short`)
- `learner_level` (`beginner|intermediate|advanced`)

Student sees:

- `use_rag_context`, `use_web_search`, `use_explanation_tool`, `use_score_tool`
- `top_k` is fixed to 3 in the UI
- `response_mode` is fixed to `step-by-step` in the UI

### Comparison tool

- The UI can generate a structured “Topic A vs Topic B” prompt.
- It submits through the same `/api/chat/ask` endpoint.
- When loading past sessions, prompts/answers are sanitized for readability.

### Sources rendering

- The page shows `Sources` expanders for **teacher** role messages when sources exist.

---

## 6) How progress tracking works

Implemented in [backend/routes/chat.py](backend/routes/chat.py) after each persisted chat.

- `student_profiles.xp_points` increases by 10 per chat.
- `student_profiles.subjects_enrolled` is appended with inferred subject (if new).
- `student_progress` is inserted/updated for `(student_profile_id, subject, topic)`.
- Score increments are small and based on answer length.

---

## 7) Documents and indexing (RAG)

1. Put PDFs in the correct role folder:
   - `backend/documents/students/`
   - `backend/documents/teachers/`
2. Start the backend.
3. On startup, the backend rebuilds vector collections under `backend/chroma_db/`.

---

## 8) Configuration notes

The backend reads environment variables from the project `.env` (see [backend/main.py](backend/main.py) and [backend/services/rag.py](backend/services/rag.py)).

Common variables:

- `API_BASE_URL` (used by [pages/chatbot.py](pages/chatbot.py); if it contains `:8000`, the client tries `:8010` first, then falls back to `:8000`)
- `GROQ_API_KEY` / `OPENAI_API_KEY` (enable LLM responses)
- `GENERAL_LLM_MODEL`, `GROQ_LLM_MODEL`, `GROQ_BASE_URL`
- `HF_LOCAL_FILES_ONLY=true` (force embeddings to load from local cache only)

LangSmith tracing (optional)

- [backend/services/rag.py](backend/services/rag.py) uses `@traceable(...)` to emit observability traces for the main chain (`rag.answer_with_agent_loop`) and key tools (`rag.content_retrieval`, `rag.duckduckgo_search`, `rag.user_score_lookup`, plus the exported `tool.*` wrappers).
- This is for debugging/performance visibility (tool routing, timings, failures) and does not change chatbot outputs.
- Tracing is active only when the relevant LangSmith/LangChain environment variables are configured (API key + tracing enabled).

Note: most other Streamlit pages currently use a hardcoded `http://127.0.0.1:8000` base URL.

---

## 9) Tests

Pytest-based unit tests exist under `tests/` (RAG routing, web search behavior, comparison chunking, etc.).

Runner:

- `tests/run_all_tests.py`
