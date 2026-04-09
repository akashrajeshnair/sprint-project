# import os
# from pathlib import Path

# import requests
# import streamlit as st
# from dotenv import load_dotenv

# BASE_DIR = Path(__file__).resolve().parent
# env_path = BASE_DIR / ".env"
# env_example_path = BASE_DIR / ".env.example"

# if env_path.exists():
#     load_dotenv(env_path)
# elif env_example_path.exists():
#     load_dotenv(env_example_path)

# API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# st.set_page_config(page_title="LLM Token Tracker", page_icon="🧮", layout="centered")
# st.title("LLM Token Tracker")
# st.caption("Select a model name to view remaining tokens, or add a new model.")


# def fetch_llms():
#     response = requests.get(f"{API_BASE_URL}/llms", timeout=10)
#     response.raise_for_status()
#     return response.json()


# def create_llm(model_name: str, total_tokens: int, tokens_used: int):
#     payload = {
#         "model_name": model_name,
#         "total_tokens": total_tokens,
#         "tokens_used": tokens_used,
#     }
#     response = requests.post(f"{API_BASE_URL}/llms", json=payload, timeout=10)
#     return response


# try:
#     llm_rows = fetch_llms()
# except requests.RequestException as exc:
#     st.error(f"Could not fetch data from API: {exc}")
#     llm_rows = []

# st.subheader("Check Tokens Left")
# if llm_rows:
#     names = [item["model_name"] for item in llm_rows]
#     selected_name = st.selectbox("Select LLM model", options=names)
#     selected = next(item for item in llm_rows if item["model_name"] == selected_name)
#     tokens_left = selected["total_tokens"] - selected["tokens_used"]

#     col1, col2, col3 = st.columns(3)
#     col1.metric("Tokens Left", f"{tokens_left:,}")
#     col2.metric("Total Tokens", f"{selected['total_tokens']:,}")
#     col3.metric("Tokens Used", f"{selected['tokens_used']:,}")
# else:
#     st.info("No LLM records found. Add one below.")

# st.divider()
# st.subheader("Add New LLM")
# with st.form("add_llm_form"):
#     model_name = st.text_input("Model Name", placeholder="gpt-4o-mini")
#     total_tokens = st.number_input("Total Tokens", min_value=0, step=1, value=1)
#     tokens_used = st.number_input("Tokens Used", min_value=0, step=1, value=0)
#     submitted = st.form_submit_button("Add LLM")

# if submitted:
#     if not model_name.strip():
#         st.warning("Model name is required.")
#     elif tokens_used > total_tokens:
#         st.warning("Tokens Used cannot be greater than Total Tokens.")
#     else:
#         try:
#             result = create_llm(model_name.strip(), int(total_tokens), int(tokens_used))
#             if result.status_code == 201:
#                 st.success("LLM added successfully.")
#                 st.rerun()
#             else:
#                 detail = result.json().get("detail", result.text)
#                 st.error(f"Failed to add LLM: {detail}")
#         except requests.RequestException as exc:
#             st.error(f"Could not connect to API: {exc}")

import requests
import streamlit as st

st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")

API_BASE_URL = "http://127.0.0.1:8000"

if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "role" not in st.session_state:
    st.session_state.role = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

st.title("Login")

with st.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

if submitted:
    if not email or not password:
        st.warning("Please enter both email and password.")
    else:
        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/login",
                json={"email": email, "password": password},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state.access_token = data["access_token"]
                st.session_state.role = data["role"]
                st.session_state.user_id = data["user_id"]

                st.success(f"Login successful as {data['role'].capitalize()}")

                # Role based navigation
                if data["role"] == "student":
                    st.switch_page("pages/student_dashboard.py")
                elif data["role"] == "teacher":
                    st.switch_page("pages/teacher_dashboard.py")
                elif data["role"] == "admin":
                    st.switch_page("pages/admin_dashboard.py")
            else:
                detail = response.json().get("detail", "Login failed")
                st.error(detail)

        except requests.exceptions.ConnectionError:
            st.error("FastAPI server is not running.")
        except Exception as e:
            st.error(f"Error: {str(e)}")