import streamlit as st

# --- AUTH CHECK ---
if "role" not in st.session_state or st.session_state.role != "student":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="Student Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 20% 20%, #1c2638 0%, #0f1420 45%, #0a0f19 100%);
        color: #e9edf7;
    }
    .hero {
        background: linear-gradient(120deg, #2d3f6f 0%, #1f2c4d 100%);
        color: #ffffff;
        padding: 1.1rem 1.3rem;
        border-radius: 14px;
        margin-bottom: 0.9rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35);
    }
    .card {
        background: #121a2a;
        border: 1px solid #2f3d56;
        border-radius: 12px;
        padding: 0.8rem 0.95rem;
        margin-bottom: 0.5rem;
    }
    .label {
        color: #aab9d6;
        font-size: 0.85rem;
        margin-bottom: 0.2rem;
    }
    .value {
        color: #f1f5ff;
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="hero">
        <h2 style="margin:0;">Student Dashboard</h2>
        <p style="margin:0.25rem 0 0 0; opacity:0.92;">Welcome back. Continue learning, track progress, and stay consistent.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

meta_col1, meta_col2 = st.columns(2)
with meta_col1:
    st.markdown(
        f"""
        <div class="card">
            <div class="label">Student ID</div>
            <p class="value">{st.session_state.user_id}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with meta_col2:
    st.markdown(
        """
        <div class="card">
            <div class="label">Today</div>
            <p class="value">Keep Going</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("### Quick Actions")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<div class='card'><b>Chat Assistant</b><br/>Ask doubts and get guided answers.</div>", unsafe_allow_html=True)
    if st.button("💬 Open Chatbot", use_container_width=True):
        st.switch_page("pages/chatbot.py")

with col2:
    st.markdown("<div class='card'><b>My Profile</b><br/>Update your details and preferences.</div>", unsafe_allow_html=True)
    if st.button("👤 Open Profile", use_container_width=True):
        st.switch_page("pages/student_profile.py")

with col3:
    st.markdown("<div class='card'><b>Sign Out</b><br/>Securely end this session.</div>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("streamlit_app.py")

