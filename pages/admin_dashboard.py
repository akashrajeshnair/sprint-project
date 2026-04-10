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

st.title("🛠 Admin Dashboard")
st.write(f"Welcome Admin | User ID: {st.session_state.user_id}")

st.divider()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🎓 View Students", use_container_width=True):
        st.switch_page("pages/admin_view_students.py")

with col2:
    if st.button("👩‍🏫 View Teachers", use_container_width=True):
        st.switch_page("pages/admin_view_teachers.py")

with col3:
    if st.button("➕ Add New User", use_container_width=True):
        st.switch_page("pages/admin_add_user.py")

with col4:
    if st.button("👥 Manage Users", use_container_width=True):
        st.switch_page("pages/admin_manage_users.py")

with col5:
    if st.button("💬 Chatbot", use_container_width=True):
        st.switch_page("pages/chatbot.py")

st.divider()

st.subheader("Admin Panel")
st.write("Use the above options to manage users.")