# import streamlit as st

# # --- AUTH CHECK ---
# if "role" not in st.session_state or st.session_state.role != "admin":
#     st.switch_page("streamlit_app.py")

# st.set_page_config(page_title="Admin Dashboard", layout="wide")

# st.title("🛠 Admin Dashboard")
# st.write(f"Welcome Admin | User ID: {st.session_state.user_id}")

# st.divider()

# col1, col2 = st.columns(2)

# with col1:
#     if st.button("➕ Add New User", use_container_width=True):
#         st.switch_page("pages/admin_add_user.py")

# with col2:
#     if st.button("💬 Chatbot", use_container_width=True):
#         st.info("Chatbot integration will be added later by teammate.")

# st.divider()

# st.subheader("Admin Panel")
# st.write("Use the above options to manage users.")

import streamlit as st

if "role" not in st.session_state or st.session_state.role != "admin":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="Admin Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 20% 20%, #2a221a 0%, #1b140f 50%, #120d09 100%);
        color: #f0e9e3;
    }
    .hero {
        background: linear-gradient(120deg, #6d3d1f 0%, #3f2515 100%);
        color: #ffffff;
        padding: 1.1rem 1.3rem;
        border-radius: 14px;
        margin-bottom: 0.9rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35);
    }
    .card {
        background: #201810;
        border: 1px solid #4a3524;
        border-radius: 12px;
        padding: 0.8rem 0.95rem;
        margin-bottom: 0.5rem;
    }
    .label {
        color: #d4b59d;
        font-size: 0.85rem;
        margin-bottom: 0.2rem;
    }
    .value {
        color: #fff4ec;
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
        <h2 style="margin:0;">Admin Dashboard</h2>
        <p style="margin:0.25rem 0 0 0; opacity:0.92;">Manage users, monitor platform operations, and keep everything in control.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

meta_col1, meta_col2 = st.columns(2)
with meta_col1:
    st.markdown(
        f"""
        <div class="card">
            <div class="label">Admin ID</div>
            <p class="value">{st.session_state.user_id}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with meta_col2:
    st.markdown(
        """
        <div class="card">
            <div class="label">Control Center</div>
            <p class="value">User Operations</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("### Quick Actions")
row1_col1, row1_col2, row1_col3 = st.columns(3)
row2_col1, row2_col2 = st.columns(2)
row3_col1, row3_col2 = st.columns(2)

with row1_col1:
    st.markdown("<div class='card'><b>Students</b><br/>View all student records and details.</div>", unsafe_allow_html=True)
    if st.button("🎓 View Students", use_container_width=True):
        st.switch_page("pages/admin_view_students.py")

with row1_col2:
    st.markdown("<div class='card'><b>Teachers</b><br/>View all teacher records and details.</div>", unsafe_allow_html=True)
    if st.button("👩‍🏫 View Teachers", use_container_width=True):
        st.switch_page("pages/admin_view_teachers.py")

with row1_col3:
    st.markdown("<div class='card'><b>Add User</b><br/>Create new student, teacher, or admin users.</div>", unsafe_allow_html=True)
    if st.button("➕ Add New User", use_container_width=True):
        st.switch_page("pages/admin_add_user.py")

with row2_col1:
    st.markdown("<div class='card'><b>Manage Users</b><br/>Edit, review, and maintain user data.</div>", unsafe_allow_html=True)
    if st.button("👥 Manage Users", use_container_width=True):
        st.switch_page("pages/admin_manage_users.py")

with row2_col2:
    st.markdown("<div class='card'><b>Chat Assistant</b><br/>Open chatbot for quick platform support.</div>", unsafe_allow_html=True)
    if st.button("💬 Open Chatbot", use_container_width=True):
        st.switch_page("pages/chatbot.py")

with row3_col1:
    st.markdown("<div class='card'><b>Sign Out</b><br/>End the admin session securely.</div>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("streamlit_app.py")