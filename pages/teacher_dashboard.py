import streamlit as st

# --- AUTH CHECK ---
if "role" not in st.session_state or st.session_state.role != "teacher":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="Teacher Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 20% 20%, #1a2a22 0%, #101b16 48%, #0b120f 100%);
        color: #e8f0ea;
    }
    .hero {
        background: linear-gradient(120deg, #23533b 0%, #183728 100%);
        color: #ffffff;
        padding: 1.1rem 1.3rem;
        border-radius: 14px;
        margin-bottom: 0.9rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35);
    }
    .card {
        background: #121d17;
        border: 1px solid #31493d;
        border-radius: 12px;
        padding: 0.8rem 0.95rem;
        margin-bottom: 0.5rem;
    }
    .label {
        color: #abc9b6;
        font-size: 0.85rem;
        margin-bottom: 0.2rem;
    }
    .value {
        color: #f0f7f2;
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h2 style="margin:0;">Teacher Dashboard</h2>
        <p style="margin:0.25rem 0 0 0; opacity:0.92;">Guide learners, monitor progress, and stay organized.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

meta_col1, meta_col2 = st.columns(2)
with meta_col1:
    st.markdown(
        f"""
        <div class="card">
            <div class="label">Teacher ID</div>
            <p class="value">{st.session_state.user_id}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with meta_col2:
    st.markdown(
        """
        <div class="card">
            <div class="label">Role Focus</div>
            <p class="value">Mentor Mode</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("### Quick Actions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("<div class='card'><b>Teaching Chatbot</b><br/>Resolve doubts and explain concepts.</div>", unsafe_allow_html=True)
    if st.button("💬 Open Chatbot", use_container_width=True):
        st.switch_page("pages/chatbot.py")

with col2:
    st.markdown("<div class='card'><b>My Profile</b><br/>Manage your teacher profile settings.</div>", unsafe_allow_html=True)
    if st.button("👤 Open Profile", use_container_width=True):
        st.switch_page("pages/teacher_profile.py")

with col3:
    st.markdown("<div class='card'><b>Student Progress</b><br/>Review learning progress and trends.</div>", unsafe_allow_html=True)
    if st.button("📊 View Student Progress", use_container_width=True):
        st.switch_page("pages/teacher_student_progress.py")

with col4:
    st.markdown("<div class='card'><b>Sign Out</b><br/>Securely end this session.</div>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("streamlit_app.py")