import os

import requests
import pandas as pd
import streamlit as st

if "role" not in st.session_state or st.session_state.role != "admin":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="Manage Users", layout="wide")

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

st.title("👥 Manage All Users")

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
    response = requests.get(f"{API_BASE_URL}/users", timeout=10)

    if response.status_code != 200:
        st.error("Failed to fetch users")
        st.stop()

    users = response.json()

except requests.exceptions.ConnectionError:
    st.error("FastAPI server is not running.")
    st.stop()
except Exception as e:
    st.error(str(e))
    st.stop()

if not users:
    st.info("No users found.")
    st.stop()

st.subheader("All Users")

df = pd.DataFrame(users)
st.dataframe(df, use_container_width=True)

st.divider()
st.subheader("Update or Delete User")

user_options = {
    f"{u['user_id']} - {u['name']} ({u['role']})": u
    for u in users
}

selected_label = st.selectbox("Select User", list(user_options.keys()))
selected_user = user_options[selected_label]

with st.form("update_user_form"):
    name = st.text_input("Name", value=selected_user["name"])
    email = st.text_input("Email", value=selected_user["email"])
    role = st.selectbox(
        "Role",
        ["student", "teacher", "admin"],
        index=["student", "teacher", "admin"].index(selected_user["role"])
    )
    subject = st.text_input(
        "Subject (required only for teacher)",
        value=selected_user["subject"] if selected_user["subject"] else ""
    )

    update_submitted = st.form_submit_button("Update User")

if update_submitted:
    if not name or not email or not role:
        st.warning("Please fill all required fields.")
    elif role == "teacher" and not subject:
        st.warning("Subject is required for teacher.")
    else:
        payload = {
            "name": name,
            "email": email,
            "role": role,
            "subject": subject if role == "teacher" else None
        }

        try:
            response = requests.put(
                f"{API_BASE_URL}/users/{selected_user['user_id']}",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                st.success("User updated successfully.")
                st.rerun()
            else:
                try:
                    st.error(response.json().get("detail", "Failed to update user"))
                except Exception:
                    st.error("Failed to update user")

        except requests.exceptions.ConnectionError:
            st.error("FastAPI server is not running.")
        except Exception as e:
            st.error(str(e))

st.divider()
st.subheader("Delete User")

if selected_user["role"] == "admin":
    st.info("Admin users cannot be deleted.")
else:
    if selected_user["user_id"] == st.session_state.user_id:
        st.info("You cannot delete your own logged-in admin account.")
    else:
        if st.button("🗑 Delete Selected User", use_container_width=True):
            try:
                response = requests.delete(
                    f"{API_BASE_URL}/users/{selected_user['user_id']}",
                    timeout=10
                )

                if response.status_code == 200:
                    st.success("User deleted successfully.")
                    st.rerun()
                else:
                    try:
                        st.error(response.json().get("detail", "Failed to delete user"))
                    except Exception:
                        st.error("Failed to delete user")

            except requests.exceptions.ConnectionError:
                st.error("FastAPI server is not running.")
            except Exception as e:
                st.error(str(e))