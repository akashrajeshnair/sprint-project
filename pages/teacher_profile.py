import requests
import streamlit as st

# --- AUTH CHECK ---
if "role" not in st.session_state or st.session_state.role != "teacher":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="Teacher Profile", layout="centered")

API_BASE_URL = "http://127.0.0.1:8000"

st.title("👤 Teacher Profile")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("⬅ Back to Dashboard", use_container_width=True):
        st.switch_page("pages/teacher_dashboard.py")

with col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("streamlit_app.py")

st.divider()

try:
    response = requests.get(
        f"{API_BASE_URL}/users/{st.session_state.user_id}",
        timeout=10
    )

    if response.status_code == 200:
        user = response.json()

        st.subheader("Teacher Details")
        st.write(f"**User ID:** {user.get('user_id', 'N/A')}")
        st.write(f"**Name:** {user.get('name', 'N/A')}")
        st.write(f"**Email:** {user.get('email', 'N/A')}")
        st.write(f"**Role:** {user.get('role', 'N/A')}")
        st.write(f"**Subject:** {user.get('subject', 'N/A')}")
    else:
        try:
            detail = response.json().get("detail", "Failed to fetch profile details")
        except Exception:
            detail = "Failed to fetch profile details"
        st.error(detail)

except requests.exceptions.ConnectionError:
    st.error("FastAPI server is not running.")
except Exception as e:
    st.error(str(e))