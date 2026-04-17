import os

import requests
import streamlit as st

# --- AUTH CHECK ---
if "role" not in st.session_state or st.session_state.role != "admin":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="Add New User", layout="centered")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 20% 20%, #2a221a 0%, #1b140f 50%, #120d09 100%);
        color: #f0e9e3;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

st.title("➕ Add New User")

col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Dashboard", use_container_width=True):
        st.switch_page("pages/admin_dashboard.py")

with col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("streamlit_app.py")

st.divider()

# ✅ FORM START
with st.form("add_user_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["student", "teacher"])
    subject = st.text_input("Subject (required only for teacher)")

    submitted = st.form_submit_button("Add User")

    # ✅ HANDLE SUBMISSION INSIDE FORM
    if submitted:
        if not name or not email or not password:
            st.warning("Please fill all required fields.")

        elif role == "teacher" and not subject:
            st.warning("Subject is required for teacher.")

        else:
            payload = {
                "name": name,
                "email": email,
                "password": password,
                "role": role,
                "subject": subject if role == "teacher" else None
            }

            try:
                response = requests.post(
                    f"{API_BASE_URL}/users/",
                    json=payload,
                    timeout=10
                )

                if response.status_code in [200, 201]:
                    st.success("✅ User added successfully.")
                else:
                    try:
                        st.error(response.json().get("detail", "Failed to add user"))
                    except:
                        st.error("Failed to add user")

            except requests.exceptions.ConnectionError:
                st.error("❌ FastAPI server is not running.")
            except Exception as e:
                st.error(str(e))