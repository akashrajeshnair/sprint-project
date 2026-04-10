import os

import requests
import streamlit as st

st.set_page_config(page_title="Chatbot", page_icon="💬", layout="wide")

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
ALLOWED_ROLES = {"student", "teacher"}


def _candidate_api_bases() -> list[str]:
    bases = [API_BASE_URL.rstrip("/")]
    if ":8000" in bases[0]:
        bases.append(bases[0].replace(":8000", ":8010"))
    return list(dict.fromkeys(bases))


def _auth_headers() -> dict[str, str]:
    token = st.session_state.get("access_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _ensure_chat_session() -> int | None:
    user_id = st.session_state.get("user_id")
    role = (st.session_state.get("role") or "student").strip().lower()
    existing = st.session_state.get("chat_session_id")

    if existing:
        return int(existing)

    payload = {
        "user_id": int(user_id),
        "subject": "General",
        "topic": "Chat",
        "difficulty_level": "beginner",
    }

    response = requests.post(
        f"{API_BASE_URL}/api/sessions",
        json=payload,
        headers=_auth_headers(),
        timeout=15,
    )
    response.raise_for_status()

    session_id = int(response.json()["session_id"])
    st.session_state.chat_session_id = session_id
    st.session_state.chat_messages = []
    st.session_state.chat_owner_role = role
    return session_id


def _reset_chat_session() -> None:
    st.session_state.chat_session_id = None
    st.session_state.chat_messages = []


def _load_chat_logs(session_id: int) -> list[dict]:
    response = requests.get(
        f"{API_BASE_URL}/api/sessions/{session_id}/messages",
        headers=_auth_headers(),
        timeout=15,
    )
    response.raise_for_status()
    rows = response.json() or []
    logs: list[dict] = []
    for row in rows:
        message_role = str(row.get("role") or "assistant").strip().lower()
        if message_role not in {"user", "assistant", "system"}:
            message_role = "assistant"
        logs.append(
            {
                "role": message_role,
                "content": row.get("content") or "",
                "sources": [],
            }
        )
    return logs


def _fetch_user_sessions(user_id: int) -> list[dict]:
    response = requests.get(
        f"{API_BASE_URL}/api/sessions",
        params={"user_id": int(user_id)},
        headers=_auth_headers(),
        timeout=15,
    )
    response.raise_for_status()
    return response.json() or []


def _delete_chat_session(session_id: int, user_id: int) -> None:
    last_error: Exception | None = None
    for base_url in _candidate_api_bases():
        try:
            response = requests.delete(
                f"{base_url}/api/sessions/{int(session_id)}",
                params={"user_id": int(user_id)},
                headers=_auth_headers(),
                timeout=15,
            )
            if response.status_code == 405:
                continue
            response.raise_for_status()
            return
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise last_error


def _format_session_label(session_row: dict) -> str:
    session_id = session_row.get("session_id")
    subject = session_row.get("subject") or "General"
    topic = session_row.get("topic") or "Chat"
    updated_at = session_row.get("updated_at") or session_row.get("started_at") or ""
    tail = f" | {updated_at}" if updated_at else ""
    return f"#{session_id} • {subject} / {topic}{tail}"


role = (st.session_state.get("role") or "").strip().lower()
user_id = st.session_state.get("user_id")

if role not in ALLOWED_ROLES or not user_id:
    st.warning("Please login as student or teacher to use chatbot.")
    st.switch_page("streamlit_app.py")

if st.session_state.get("chat_owner_role") and st.session_state.get("chat_owner_role") != role:
    _reset_chat_session()

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = None

if st.session_state.chat_session_id and not st.session_state.chat_messages:
    try:
        st.session_state.chat_messages = _load_chat_logs(int(st.session_state.chat_session_id))
    except Exception:
        st.session_state.chat_messages = []

st.title("💬 Learning Chatbot")
st.caption(f"Logged in as **{role.capitalize()}** | User ID: **{user_id}**")

nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 2])
with nav_col1:
    if st.button("⬅ Back to Dashboard", use_container_width=True):
        if role == "student":
            st.switch_page("pages/student_dashboard.py")
        else:
            st.switch_page("pages/teacher_dashboard.py")
with nav_col2:
    if st.button("🧹 New Chat", use_container_width=True):
        _reset_chat_session()
        st.rerun()
with nav_col3:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("streamlit_app.py")

with st.sidebar:
    st.subheader("Previous Sessions")
    sessions: list[dict] = []
    try:
        sessions = _fetch_user_sessions(int(user_id))
    except Exception:
        sessions = []

    if sessions:
        options = { _format_session_label(row): int(row.get("session_id")) for row in sessions if row.get("session_id") }
        labels = list(options.keys())

        current_session_id = st.session_state.get("chat_session_id")
        default_index = 0
        if current_session_id:
            for i, label in enumerate(labels):
                if options[label] == int(current_session_id):
                    default_index = i
                    break

        selected_label = st.selectbox("Choose a previous session", labels, index=default_index)
        selected_session_id = options[selected_label]

        if st.button("Load Selected Session", use_container_width=True):
            st.session_state.chat_session_id = selected_session_id
            st.session_state.chat_messages = _load_chat_logs(selected_session_id)
            st.session_state.chat_owner_role = role
            st.rerun()

        if st.button("🗑 Delete Selected Session", use_container_width=True):
            try:
                _delete_chat_session(selected_session_id, int(user_id))
                if st.session_state.get("chat_session_id") == selected_session_id:
                    _reset_chat_session()
                st.success("Session deleted.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not delete session: {exc}")
    else:
        st.caption("No previous sessions found for this user yet.")

    st.divider()
    st.subheader("Chat Settings")
    if role == "teacher":
        use_rag_context = st.toggle("Use RAG context", value=True)
        top_k = st.slider("Top K sources", min_value=1, max_value=8, value=3)
        response_mode = st.selectbox("Response mode", options=["step-by-step", "short"], index=0)
        learner_level = st.selectbox("Learner level", options=["beginner", "intermediate", "advanced"], index=0)
    else:
        use_rag_context = True
        top_k = 3
        response_mode = "step-by-step"
        learner_level = "beginner"
        st.caption("Default chat settings are applied for students.")

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if role == "teacher" and msg.get("sources"):
            with st.expander("Sources"):
                for idx, src in enumerate(msg["sources"], start=1):
                    source_name = src.get("source", "unknown")
                    snippet = src.get("snippet", "")
                    st.markdown(f"**{idx}. {source_name}**")
                    if snippet:
                        st.caption(snippet)

with st.expander("📜 Chat Logs", expanded=False):
    if not st.session_state.chat_messages:
        st.caption("No messages yet.")
    else:
        for idx, msg in enumerate(st.session_state.chat_messages, start=1):
            msg_role = str(msg.get("role") or "assistant").capitalize()
            content = msg.get("content") or ""
            st.markdown(f"**{idx}. {msg_role}:** {content}")

prompt = st.chat_input("Ask a question...")

if prompt:
    st.session_state.chat_messages.append({"role": "user", "content": prompt})

    try:
        session_id = _ensure_chat_session()
        if not session_id:
            raise RuntimeError("Unable to create chat session.")

        payload = {
            "session_id": session_id,
            "question": prompt,
            "role": role,
            "learner_level": learner_level,
            "response_mode": response_mode,
            "selected_file": None,
            "use_rag_context": use_rag_context,
            "top_k": top_k,
            "persist_messages": True,
        }

        response = requests.post(
            f"{API_BASE_URL}/api/chat/ask",
            json=payload,
            headers=_auth_headers(),
            timeout=30,
        )

        if response.status_code != 200:
            detail = "Chat request failed"
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                detail = response.text or detail
            raise RuntimeError(detail)

        data = response.json()
        answer = data.get("answer") or "I could not generate a response."
        sources = data.get("sources", [])
        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": answer,
                "sources": sources,
            }
        )
    except requests.exceptions.ConnectionError:
        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": "Could not connect to FastAPI server.",
                "sources": [],
            }
        )
    except Exception as exc:
        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": f"Error: {exc}",
                "sources": [],
            }
        )

    st.rerun()
