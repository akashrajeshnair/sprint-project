import streamlit as st

# --- AUTH CHECK ---
if "role" not in st.session_state or st.session_state.role != "student":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="Student Dashboard", layout="wide")

st.title("🎓 Student Dashboard")

st.write(f"Welcome User ID: {st.session_state.user_id}")

st.divider()

# --- NAVIGATION BUTTONS ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💬 Chatbot"):
        st.info("Chatbot integration will be added by teammate")

with col2:
    if st.button("👤 Profile"):
        st.switch_page("pages/student_profile.py")

with col3:
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.switch_page("streamlit_app.py")

st.divider()

# --- DASHBOARD CONTENT (placeholder) ---
st.subheader("📊 Student Overview")

st.write("This is your dashboard. More features will be added soon.")