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
        f"{API_BASE_URL}/users/by-id/{st.session_state.user_id}",
        timeout=10
    )

    if response.status_code == 200:
        user = response.json()

        # ---------------- BASIC INFO ----------------
        st.subheader("📌 Basic Information")

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Name:** {user.get('name', 'N/A')}")
            st.write(f"**Email:** {user.get('email', 'N/A')}")

        with col2:
            st.write(f"**Role:** {user.get('role', 'N/A')}")
            st.write(f"**Subject:** {user.get('subject', 'N/A')}")

        st.divider()

        # ---------------- STUDENT PROFILE ----------------
        st.subheader("🎓 Academic Details")

        col3, col4 = st.columns(2)
        with col3:
            st.write(f"**Grade Level:** {user.get('grade_level', 'N/A')}")
            st.write(f"**Learning Style:** {user.get('learning_style', 'N/A')}")

        with col4:
            st.write(f"**XP Points:** {user.get('xp_points', 0)}")
            st.write(f"**Last Active:** {user.get('last_active_at', 'N/A')}")

        st.divider()

        # ---------------- SUBJECTS ----------------
        st.subheader("📚 Subjects Enrolled")

        subjects = user.get("subjects_enrolled", [])

        if isinstance(subjects, list) and subjects:
            for sub in subjects:
                st.markdown(f"- {sub}")
        else:
            st.write("N/A")

    else:
        st.error("Failed to fetch profile details")

except requests.exceptions.ConnectionError:
    st.error("Backend server not running")
except Exception as e:
    st.error(str(e))