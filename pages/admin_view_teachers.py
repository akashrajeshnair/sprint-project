import os
import requests
import streamlit as st

if "role" not in st.session_state or st.session_state.role != "admin":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="View Teachers", layout="wide")

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

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.title("👩‍🏫 All Teachers")

col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Dashboard", use_container_width=True):
        st.switch_page("pages/admin_dashboard.py")

with col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("streamlit_app.py")

st.divider()

try:
    response = requests.get(f"{API_BASE_URL}/teachers", timeout=10)

    if response.status_code == 200:
        teachers = response.json()

        if teachers:
            for teacher in teachers:
                with st.container(border=True):
                    st.write(f"**User ID:** {teacher.get('user_id', 'N/A')}")
                    st.write(f"**Name:** {teacher.get('name', 'N/A')}")
                    st.write(f"**Email:** {teacher.get('email', 'N/A')}")
                    st.write(f"**Role:** {teacher.get('role', 'N/A')}")
                    st.write(f"**Subject:** {teacher.get('subject', 'N/A')}")
        else:
            st.info("No teachers found.")
    else:
        st.error(f"Failed to fetch teachers. Status code: {response.status_code}")
        try:
            st.write(response.json())
        except Exception:
            st.write(response.text)

except requests.exceptions.ConnectionError:
    st.error("FastAPI server is not running.")
except Exception as e:
    st.error(str(e))