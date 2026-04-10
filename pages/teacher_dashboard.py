import streamlit as st

# --- AUTH CHECK ---
if "role" not in st.session_state or st.session_state.role != "teacher":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="Teacher Dashboard", layout="wide")

st.title("👩‍🏫 Teacher Dashboard")
st.write(f"Welcome, Teacher | User ID: {st.session_state.user_id}")

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("💬 Chatbot", use_container_width=True):
        st.switch_page("pages/chatbot.py")

with col2:
    if st.button("👤 My Profile", use_container_width=True):
        st.switch_page("pages/teacher_profile.py")

with col3:
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.switch_page("streamlit_app.py")

with col4:
    if st.button("📊 Student Progress", use_container_width=True):
        st.switch_page("pages/teacher_student_progress.py")

st.divider()