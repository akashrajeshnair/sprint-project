import os

import requests
import streamlit as st

if "role" not in st.session_state or st.session_state.role != "admin":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="View Students", layout="wide")

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

st.title("🎓 All Students")

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
    response = requests.get(f"{API_BASE_URL}/students", timeout=10)

    if response.status_code == 200:
        students = response.json()

        if students:
            for student in students:
                with st.container(border=True):
                    st.write(f"**User ID:** {student.get('user_id', 'N/A')}")
                    st.write(f"**Name:** {student.get('name', 'N/A')}")
                    st.write(f"**Email:** {student.get('email', 'N/A')}")
                    st.write(f"**Role:** {student.get('role', 'N/A')}")
        else:
            st.info("No students found.")
    else:
        st.error(f"Failed to fetch students. Status code: {response.status_code}")
        try:
            st.write(response.json())
        except Exception:
            st.write(response.text)

except requests.exceptions.ConnectionError:
    st.error("FastAPI server is not running.")
except Exception as e:
    st.error(str(e))