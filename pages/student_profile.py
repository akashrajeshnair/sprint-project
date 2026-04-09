import streamlit as st
import requests

# --- AUTH CHECK ---
if "role" not in st.session_state or st.session_state.role != "student":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="Student Profile", layout="centered")

API_BASE_URL = "http://127.0.0.1:8000"

st.title("👤 Student Profile")

# --- BACK BUTTON ---
if st.button("⬅ Back to Dashboard"):
    st.switch_page("pages/student_dashboard.py")

st.divider()

# --- FETCH USER DATA ---
try:
    response = requests.get(
        f"{API_BASE_URL}/users/{st.session_state.user_id}",
        timeout=10
    )

    if response.status_code == 200:
        user = response.json()

        st.subheader("Basic Information")

        st.write(f"**Name:** {user.get('name', 'N/A')}")
        st.write(f"**Email:** {user.get('email', 'N/A')}")
        st.write(f"**Role:** {user.get('role', 'N/A')}")

        # Optional fields
        st.write(f"**Subject:** {user.get('subject', 'N/A')}")

    else:
        st.error("Failed to fetch profile details")

except requests.exceptions.ConnectionError:
    st.error("Backend server not running")
except Exception as e:
    st.error(str(e))