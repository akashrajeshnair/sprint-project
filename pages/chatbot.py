# import os
# import re

# import requests
# import streamlit as st

# st.set_page_config(page_title="Chatbot", page_icon="💬", layout="wide")

# API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
# ALLOWED_ROLES = {"student", "teacher"}


# def _candidate_api_bases() -> list[str]:
#     bases = [API_BASE_URL.rstrip("/")]
#     if ":8000" in bases[0]:
#         bases = [bases[0].replace(":8000", ":8010"), bases[0]]
#     return list(dict.fromkeys(bases))


# def _api_request(method: str, path: str, *, params: dict | None = None, json_body: dict | None = None, timeout: int = 15):
#     last_error: Exception | None = None
#     for base_url in _candidate_api_bases():
#         try:
#             response = requests.request(
#                 method=method,
#                 url=f"{base_url}{path}",
#                 params=params,
#                 json=json_body,
#                 headers=_auth_headers(),
#                 timeout=timeout,
#             )
#             if response.status_code == 405:
#                 continue
#             return response
#         except Exception as exc:
#             last_error = exc

#     if last_error is not None:
#         raise last_error
#     raise RuntimeError("Unable to reach API server")


# def _auth_headers() -> dict[str, str]:
#     token = st.session_state.get("access_token")
#     if not token:
#         return {}
#     return {"Authorization": f"Bearer {token}"}


# def _ensure_chat_session(is_comparison: bool = False) -> int | None:
#     user_id = st.session_state.get("user_id")
#     role = (st.session_state.get("role") or "student").strip().lower()
#     existing = st.session_state.get("chat_session_id")

#     if existing:
#         return int(existing)

#     payload = {
#         "user_id": int(user_id),
#         "subject": "Comparison" if is_comparison else "General",
#         "topic": "Chat",
#         "difficulty_level": "beginner",
#     }

#     response = _api_request("POST", "/api/sessions", json_body=payload, timeout=15)
#     response.raise_for_status()

#     session_id = int(response.json()["session_id"])
#     st.session_state.chat_session_id = session_id
#     st.session_state.chat_messages = []
#     st.session_state.chat_owner_role = role
#     return session_id


# def _reset_chat_session() -> None:
#     st.session_state.chat_session_id = None
#     st.session_state.chat_messages = []


# def _sanitize_comparison_user_prompt(text: str) -> str:
#     content = (text or "").strip()
#     if "Create a structured comparison between the following two topics." not in content:
#         return content

#     match_a = re.search(r"Topic A:\s*(.+)", content)
#     match_b = re.search(r"Topic B:\s*(.+)", content)
#     if match_a and match_b:
#         topic_a = match_a.group(1).strip()
#         topic_b = match_b.group(1).strip()
#         return f"Compare {topic_a} and {topic_b}"
#     return "Comparison request"


# def _format_comparison_answer(answer: str) -> str:
#     text = (answer or "").replace("\r\n", "\n").strip()
#     if not text:
#         return text

#     # Normalize common markdown variants into plain section + subpoint lines.
#     text = re.sub(r"^##\s*(.+)$", r"\1:", text, flags=re.MULTILINE)
#     text = re.sub(r"^\s*\d+\)\s*", "", text, flags=re.MULTILINE)
#     text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
#     text = text.replace("Use Cases / Comparison Criteria:", "Use Cases:")
#     text = text.replace("Brief Definitions:", "Output:")

#     markers = ["Output:", "Key Differences:", "Comparison:", "Use Cases:"]
#     for marker in markers:
#         text = re.sub(rf"(?<!\n\n){re.escape(marker)}", f"\n\n{marker}", text)

#     # Split packed inline segments into separate lines when labels are present.
#     text = re.sub(r";\s*", "\n", text)
#     text = re.sub(r"\s+([A-Z][A-Za-z0-9 /&()_-]{2,40}:)", r"\n\1", text)
#     text = re.sub(r"\n{3,}", "\n\n", text)
#     return text.strip()


# def _load_chat_logs(session_id: int) -> list[dict]:
#     response = _api_request("GET", f"/api/sessions/{session_id}/messages", timeout=15)
#     response.raise_for_status()
#     rows = response.json() or []
#     is_comparison_session = any(
#         "Create a structured comparison between the following two topics." in str(row.get("content") or "")
#         for row in rows
#     )
#     logs: list[dict] = []
#     for row in rows:
#         message_role = str(row.get("role") or "assistant").strip().lower()
#         if message_role not in {"user", "assistant", "system"}:
#             message_role = "assistant"
#         content = (row.get("content") or "")
#         if message_role == "user":
#             content = _sanitize_comparison_user_prompt(content)
#         elif message_role == "assistant" and is_comparison_session:
#             content = _format_comparison_answer(content)
#         logs.append(
#             {
#                 "role": message_role,
#                 "content": content,
#                 "sources": [],
#             }
#         )
#     return logs


# def _fetch_user_sessions(user_id: int) -> list[dict]:
#     response = _api_request("GET", "/api/sessions", params={"user_id": int(user_id)}, timeout=15)
#     response.raise_for_status()
#     return response.json() or []


# def _delete_chat_session(session_id: int, user_id: int) -> None:
#     last_error: Exception | None = None
#     for base_url in _candidate_api_bases():
#         try:
#             response = requests.delete(
#                 f"{base_url}/api/sessions/{int(session_id)}",
#                 params={"user_id": int(user_id)},
#                 headers=_auth_headers(),
#                 timeout=15,
#             )
#             if response.status_code == 405:
#                 continue
#             response.raise_for_status()
#             return
#         except Exception as exc:
#             last_error = exc

#     if last_error is not None:
#         raise last_error


# def _format_session_label(session_row: dict) -> str:
#     session_id = session_row.get("session_id")
#     subject = session_row.get("subject") or "General"
#     topic = session_row.get("topic") or "Chat"
#     updated_at = session_row.get("updated_at") or session_row.get("started_at") or ""
#     tail = f" | {updated_at}" if updated_at else ""
    
#     # Display "Comparison Chat" for comparison sessions
#     if subject.lower() == "comparison":
#         return f"#{session_id} • Comparison Chat{tail}"
#     return f"#{session_id} • {subject} / {topic}{tail}"


# role = (st.session_state.get("role") or "").strip().lower()
# user_id = st.session_state.get("user_id")

# if role not in ALLOWED_ROLES or not user_id:
#     st.warning("Please login as student or teacher to use chatbot.")
#     st.switch_page("streamlit_app.py")

# if st.session_state.get("chat_owner_role") and st.session_state.get("chat_owner_role") != role:
#     _reset_chat_session()

# if "chat_messages" not in st.session_state:
#     st.session_state.chat_messages = []
# if "chat_session_id" not in st.session_state:
#     st.session_state.chat_session_id = None
# if "comparison_mode" not in st.session_state:
#     st.session_state.comparison_mode = False

# if st.session_state.chat_session_id and not st.session_state.chat_messages:
#     try:
#         st.session_state.chat_messages = _load_chat_logs(int(st.session_state.chat_session_id))
#     except Exception:
#         st.session_state.chat_messages = []

# st.title("💬 Learning Chatbot")
# st.caption(f"Logged in as **{role.capitalize()}** | User ID: **{user_id}**")

# nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 2])
# with nav_col1:
#     if st.button("⬅ Back to Dashboard", use_container_width=True):
#         if role == "student":
#             st.switch_page("pages/student_dashboard.py")
#         else:
#             st.switch_page("pages/teacher_dashboard.py")
# with nav_col2:
#     if st.button("🧹 New Chat", use_container_width=True):
#         _reset_chat_session()
#         st.session_state.comparison_mode = False
#         st.rerun()
# with nav_col3:
#     if st.button("🆚 Comparison Tool", use_container_width=True):
#         _reset_chat_session()
#         st.session_state.comparison_mode = True
#         st.rerun()
# with nav_col4:
#     if st.button("🚪 Logout", use_container_width=True):
#         st.session_state.clear()
#         st.switch_page("streamlit_app.py")

# with st.sidebar:
#     st.subheader("Previous Sessions")
#     sessions: list[dict] = []
#     try:
#         sessions = _fetch_user_sessions(int(user_id))
#     except Exception:
#         sessions = []

#     if sessions:
#         options = { _format_session_label(row): int(row.get("session_id")) for row in sessions if row.get("session_id") }
#         labels = list(options.keys())

#         current_session_id = st.session_state.get("chat_session_id")
#         default_index = 0
#         if current_session_id:
#             for i, label in enumerate(labels):
#                 if options[label] == int(current_session_id):
#                     default_index = i
#                     break

#         selected_label = st.selectbox("Choose a previous session", labels, index=default_index)
#         selected_session_id = options[selected_label]

#         if st.button("Load Selected Session", use_container_width=True):
#             st.session_state.chat_session_id = selected_session_id
#             st.session_state.chat_messages = _load_chat_logs(selected_session_id)
#             st.session_state.chat_owner_role = role
#             st.session_state.comparison_mode = False
#             st.rerun()

#         if st.button("🗑 Delete Selected Session", use_container_width=True):
#             try:
#                 _delete_chat_session(selected_session_id, int(user_id))
#                 if st.session_state.get("chat_session_id") == selected_session_id:
#                     _reset_chat_session()
#                 st.success("Session deleted.")
#                 st.rerun()
#             except Exception as exc:
#                 st.error(f"Could not delete session: {exc}")
#     else:
#         st.caption("No previous sessions found for this user yet.")

#     st.divider()
#     st.subheader("Chat Settings")
#     if role == "teacher":
#         use_rag_context = st.toggle("Use RAG context", value=True)
#         top_k = st.slider("Top K sources", min_value=1, max_value=8, value=3)
#         response_mode = st.selectbox("Response mode", options=["step-by-step", "short"], index=0)
#         learner_level = st.selectbox("Learner level", options=["beginner", "intermediate", "advanced"], index=0)
#     else:
#         use_rag_context = st.toggle("Use RAG context", value=True, key="student_use_rag_context")
#         top_k = 3
#         response_mode = "step-by-step"
#         learner_level = "beginner"
#         st.caption("Turn off RAG to get a general non-RAG answer.")

# for msg in st.session_state.chat_messages:
#     with st.chat_message(msg["role"]):
#         rendered_content = (msg["content"] or "").replace("\n", "  \n")
#         st.markdown(rendered_content)
#         if role == "teacher" and msg.get("sources"):
#             with st.expander("Sources"):
#                 for idx, src in enumerate(msg["sources"], start=1):
#                     source_name = src.get("source", "unknown")
#                     snippet = src.get("snippet", "")
#                     st.markdown(f"**{idx}. {source_name}**")
#                     if snippet:
#                         st.caption(snippet)

# with st.expander("📜 Chat Logs", expanded=False):
#     if not st.session_state.chat_messages:
#         st.caption("No messages yet.")
#     else:
#         for idx, msg in enumerate(st.session_state.chat_messages, start=1):
#             msg_role = str(msg.get("role") or "assistant").capitalize()
#             content = msg.get("content") or ""
#             rendered_content = content.replace("\n", "  \n")
#             st.markdown(f"**{idx}. {msg_role}:**  \n{rendered_content}")


# def _submit_chat(
#     question: str,
#     *,
#     force_non_rag: bool = False,
#     is_comparison: bool = False,
#     display_question: str | None = None,
# ) -> None:
#     st.session_state.chat_messages.append({"role": "user", "content": display_question or question})

#     try:
#         session_id = _ensure_chat_session(is_comparison=is_comparison)
#         if not session_id:
#             raise RuntimeError("Unable to create chat session.")

#         payload = {
#             "session_id": session_id,
#             "question": question,
#             "role": role,
#             "learner_level": learner_level,
#             "response_mode": response_mode,
#             "selected_file": None,
#             "use_rag_context": False if force_non_rag else use_rag_context,
#             "top_k": top_k,
#             "persist_messages": True,
#         }

#         response = _api_request("POST", "/api/chat/ask", json_body=payload, timeout=30)

#         if response.status_code != 200:
#             detail = "Chat request failed"
#             try:
#                 detail = response.json().get("detail", detail)
#             except Exception:
#                 detail = response.text or detail
#             raise RuntimeError(detail)

#         data = response.json()
#         answer = data.get("answer") or "I could not generate a response."
#         if is_comparison:
#             answer = _format_comparison_answer(answer)
#         sources = data.get("sources", [])
#         st.session_state.chat_messages.append(
#             {
#                 "role": "assistant",
#                 "content": answer,
#                 "sources": sources,
#             }
#         )
#     except requests.exceptions.ConnectionError:
#         st.session_state.chat_messages.append(
#             {
#                 "role": "assistant",
#                 "content": "Could not connect to FastAPI server.",
#                 "sources": [],
#             }
#         )
#     except Exception as exc:
#         st.session_state.chat_messages.append(
#             {
#                 "role": "assistant",
#                 "content": f"Error: {exc}",
#                 "sources": [],
#             }
#         )


# if st.session_state.comparison_mode:
#     st.info("Comparison Tool: Start a focused comparison as a new chat.")
#     with st.form("comparison_tool_form"):
#         topic_1 = st.text_input("Topic 1", placeholder="REST")
#         topic_2 = st.text_input("Topic 2", placeholder="SOAP")
#         comparison_submit = st.form_submit_button("Generate Comparison")

#     if comparison_submit:
#         if not topic_1.strip() or not topic_2.strip():
#             st.warning("Please enter both topics.")
#         else:
#             topic_1_clean = topic_1.strip()
#             topic_2_clean = topic_2.strip()
#             comparison_prompt = (
#                 "Create a structured comparison between the following two topics.\n"
#                 f"Topic A: {topic_1_clean}\n"
#                 f"Topic B: {topic_2_clean}\n\n"
#                 "Return ONLY line-by-line output in this exact style (no paragraph blocks):\n\n"
#                 "Output:\n"
#                 f"{topic_1_clean}: one line\n"
#                 f"{topic_2_clean}: one line\n\n"
#                 "Key Differences OR Comparison:\n"
#                 "Point 1: ...\n"
#                 "Point 2: ...\n"
#                 "Point 3: ...\n\n"
#                 "Use Cases:\n"
#                 f"{topic_1_clean} for ...\n"
#                 f"{topic_2_clean} for ...\n\n"
#                 "Rules: each item must be on its own line; no single long paragraph; keep concise."
#             )
#             visible_question = f"Compare {topic_1_clean} and {topic_2_clean}"
#             _submit_chat(
#                 comparison_prompt,
#                 force_non_rag=True,
#                 is_comparison=True,
#                 display_question=visible_question,
#             )
#             st.rerun()

# prompt = st.chat_input("Ask a question...")

# if prompt:
#     _submit_chat(prompt)
#     st.rerun()

import os
import re

import requests
import streamlit as st

st.set_page_config(page_title="Chatbot", page_icon="💬", layout="wide")

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
ALLOWED_ROLES = {"student", "teacher"}


def _candidate_api_bases() -> list[str]:
    bases = [API_BASE_URL.rstrip("/")]
    if ":8000" in bases[0]:
        bases = [bases[0].replace(":8000", ":8010"), bases[0]]
    return list(dict.fromkeys(bases))


def _api_request(method: str, path: str, *, params: dict | None = None, json_body: dict | None = None, timeout: int = 15):
    last_error: Exception | None = None
    for base_url in _candidate_api_bases():
        try:
            response = requests.request(
                method=method,
                url=f"{base_url}{path}",
                params=params,
                json=json_body,
                headers=_auth_headers(),
                timeout=timeout,
            )
            if response.status_code == 405:
                continue
            return response
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    raise RuntimeError("Unable to reach API server")


def _auth_headers() -> dict[str, str]:
    token = st.session_state.get("access_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _create_fresh_chat_session(*, is_comparison: bool = False) -> int | None:
    """
    Creates a brand new session every time it is called.
    Used only for compatibility if needed elsewhere.
    """
    user_id = st.session_state.get("user_id")
    role = (st.session_state.get("role") or "student").strip().lower()

    payload = {
        "user_id": int(user_id),
        "subject": "Comparison" if is_comparison else "General",
        "topic": "Chat",
        "difficulty_level": "beginner",
    }

    response = _api_request("POST", "/api/sessions", json_body=payload, timeout=15)
    response.raise_for_status()

    session_id = int(response.json()["session_id"])
    st.session_state.chat_session_id = session_id
    st.session_state.chat_messages = []
    st.session_state.chat_owner_role = role
    return session_id


def _reset_chat_session() -> None:
    st.session_state.chat_session_id = None
    st.session_state.chat_messages = []


def _sanitize_comparison_user_prompt(text: str) -> str:
    content = (text or "").strip()
    if "Create a structured comparison between the following two topics." not in content:
        return content

    match_a = re.search(r"Topic A:\s*(.+)", content)
    match_b = re.search(r"Topic B:\s*(.+)", content)
    if match_a and match_b:
        topic_a = match_a.group(1).strip()
        topic_b = match_b.group(1).strip()
        return f"Compare {topic_a} and {topic_b}"
    return "Comparison request"


def _format_comparison_answer(answer: str) -> str:
    text = (answer or "").replace("\r\n", "\n").strip()
    if not text:
        return text

    text = re.sub(r"^##\s*(.+)$", r"\1:", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\)\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = text.replace("Use Cases / Comparison Criteria:", "Use Cases:")
    text = text.replace("Brief Definitions:", "Output:")

    markers = ["Output:", "Key Differences:", "Comparison:", "Use Cases:"]
    for marker in markers:
        text = re.sub(rf"(?<!\n\n){re.escape(marker)}", f"\n\n{marker}", text)

    text = re.sub(r";\s*", "\n", text)
    text = re.sub(r"\s+([A-Z][A-Za-z0-9 /&()_-]{2,40}:)", r"\n\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _load_chat_logs(session_id: int) -> list[dict]:
    response = _api_request("GET", f"/api/sessions/{session_id}/messages", timeout=15)
    response.raise_for_status()
    rows = response.json() or []
    is_comparison_session = any(
        "Create a structured comparison between the following two topics." in str(row.get("content") or "")
        for row in rows
    )
    logs: list[dict] = []
    for row in rows:
        message_role = str(row.get("role") or "assistant").strip().lower()
        if message_role not in {"user", "assistant", "system"}:
            message_role = "assistant"
        content = (row.get("content") or "")
        if message_role == "user":
            content = _sanitize_comparison_user_prompt(content)
        elif message_role == "assistant" and is_comparison_session:
            content = _format_comparison_answer(content)
        logs.append(
            {
                "role": message_role,
                "content": content,
                "sources": [],
            }
        )
    return logs


def _fetch_user_sessions(user_id: int) -> list[dict]:
    response = _api_request("GET", "/api/sessions", params={"user_id": int(user_id)}, timeout=15)
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

    if str(subject).lower() == "comparison":
        return f"#{session_id} • Comparison Chat{tail}"
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
if "comparison_mode" not in st.session_state:
    st.session_state.comparison_mode = False

if st.session_state.chat_session_id and not st.session_state.chat_messages:
    try:
        st.session_state.chat_messages = _load_chat_logs(int(st.session_state.chat_session_id))
    except Exception:
        st.session_state.chat_messages = []

st.title("💬 Learning Chatbot")
st.caption(f"Logged in as **{role.capitalize()}** | User ID: **{user_id}**")

nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 2])
with nav_col1:
    if st.button("⬅ Back to Dashboard", use_container_width=True):
        if role == "student":
            st.switch_page("pages/student_dashboard.py")
        else:
            st.switch_page("pages/teacher_dashboard.py")
with nav_col2:
    if st.button("🧹 New Chat", use_container_width=True):
        _reset_chat_session()
        st.session_state.comparison_mode = False
        st.rerun()
with nav_col3:
    if st.button("🆚 Comparison Tool", use_container_width=True):
        _reset_chat_session()
        st.session_state.comparison_mode = True
        st.rerun()
with nav_col4:
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
        options = {_format_session_label(row): int(row.get("session_id")) for row in sessions if row.get("session_id")}
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
            st.session_state.comparison_mode = False
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
        use_rag_context = st.toggle("Use RAG context", value=True, key="student_use_rag_context")
        top_k = 3
        response_mode = "step-by-step"
        learner_level = "beginner"
        st.caption("Turn off RAG to get a general non-RAG answer.")

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        rendered_content = (msg["content"] or "").replace("\n", "  \n")
        st.markdown(rendered_content)
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
            rendered_content = content.replace("\n", "  \n")
            st.markdown(f"**{idx}. {msg_role}:**  \n{rendered_content}")


def _submit_chat(
    question: str,
    *,
    force_non_rag: bool = False,
    is_comparison: bool = False,
    display_question: str | None = None,
) -> None:
    st.session_state.chat_messages.append({"role": "user", "content": display_question or question})

    try:
        # IMPORTANT CHANGE:
        # For every new submitted chat, do not reuse the previous session.
        # Let backend create a fresh session and infer subject/topic dynamically.
        payload = {
            "user_id": int(user_id),
            "session_id": None,
            "question": question,
            "role": role,
            "learner_level": learner_level,
            "response_mode": response_mode,
            "selected_file": None,
            "use_rag_context": False if force_non_rag else use_rag_context,
            "top_k": top_k,
            "persist_messages": True,
            "create_new_session": True,
        }

        response = _api_request("POST", "/api/chat/ask", json_body=payload, timeout=30)

        if response.status_code != 200:
            detail = "Chat request failed"
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                detail = response.text or detail
            raise RuntimeError(detail)

        data = response.json()

        # IMPORTANT CHANGE:
        # Store the new session id returned by backend so it can be shown/loaded later.
        returned_session_id = data.get("session_id")
        if returned_session_id:
            st.session_state.chat_session_id = int(returned_session_id)
            st.session_state.chat_owner_role = role

        answer = data.get("answer") or "I could not generate a response."
        subject = data.get("subject")
        topic = data.get("topic")

        if is_comparison:
            answer = _format_comparison_answer(answer)

        if subject or topic:
            meta_lines = []
            if subject:
                meta_lines.append(f"**Subject:** {subject}")
            if topic:
                meta_lines.append(f"**Topic:** {topic}")
            answer = "\n\n".join(meta_lines + [answer])

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


if st.session_state.comparison_mode:
    st.info("Comparison Tool: Start a focused comparison as a new chat.")
    with st.form("comparison_tool_form"):
        topic_1 = st.text_input("Topic 1", placeholder="REST")
        topic_2 = st.text_input("Topic 2", placeholder="SOAP")
        comparison_submit = st.form_submit_button("Generate Comparison")

    if comparison_submit:
        if not topic_1.strip() or not topic_2.strip():
            st.warning("Please enter both topics.")
        else:
            topic_1_clean = topic_1.strip()
            topic_2_clean = topic_2.strip()
            comparison_prompt = (
                "Create a structured comparison between the following two topics.\n"
                f"Topic A: {topic_1_clean}\n"
                f"Topic B: {topic_2_clean}\n\n"
                "Return ONLY line-by-line output in this exact style (no paragraph blocks):\n\n"
                "Output:\n"
                f"{topic_1_clean}: one line\n"
                f"{topic_2_clean}: one line\n\n"
                "Key Differences OR Comparison:\n"
                "Point 1: ...\n"
                "Point 2: ...\n"
                "Point 3: ...\n\n"
                "Use Cases:\n"
                f"{topic_1_clean} for ...\n"
                f"{topic_2_clean} for ...\n\n"
                "Rules: each item must be on its own line; no single long paragraph; keep concise."
            )
            visible_question = f"Compare {topic_1_clean} and {topic_2_clean}"
            _submit_chat(
                comparison_prompt,
                force_non_rag=True,
                is_comparison=True,
                display_question=visible_question,
            )
            st.rerun()

prompt = st.chat_input("Ask a question...")

if prompt:
    _submit_chat(prompt)
    st.rerun()