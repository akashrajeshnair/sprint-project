# import requests
# import pandas as pd
# import streamlit as st

# if "role" not in st.session_state or st.session_state.role != "teacher":
#     st.switch_page("streamlit_app.py")

# st.set_page_config(page_title="Student Progress", layout="wide")

# API_BASE_URL = "http://127.0.0.1:8000"

# st.title("📊 Student Progress")

# col1, col2 = st.columns(2)

# with col1:
#     if st.button("⬅ Back to Dashboard", use_container_width=True):
#         st.switch_page("pages/teacher_dashboard.py")

# with col2:
#     if st.button("🚪 Logout", use_container_width=True):
#         st.session_state.clear()
#         st.switch_page("streamlit_app.py")

# st.divider()

# try:
#     response = requests.get(f"{API_BASE_URL}/student-progress", timeout=10)

#     if response.status_code == 200:
#         progress_data = response.json()

#         if progress_data:
#             df = pd.DataFrame(progress_data)

#             if "subjects_enrolled" in df.columns:
#                 df["subjects_enrolled"] = df["subjects_enrolled"].apply(
#                     lambda x: ", ".join(x) if isinstance(x, list) else x
#                 )

#             st.dataframe(df, use_container_width=True)
#         else:
#             st.info("No student progress data found.")
#     else:
#         try:
#             st.error(response.json().get("detail", "Failed to fetch student progress"))
#         except Exception:
#             st.error("Failed to fetch student progress")

# except requests.exceptions.ConnectionError:
#     st.error("FastAPI server is not running.")
# except Exception as e:
#     st.error(str(e))

import os
import requests
import pandas as pd
import streamlit as st

if "role" not in st.session_state or st.session_state.role != "teacher":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="All Students", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 20% 20%, #1a2a22 0%, #101b16 48%, #0b120f 100%);
        color: #e8f1ea;
    }
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.45rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

st.title("📚 All Students")

col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Dashboard", use_container_width=True):
        st.switch_page("pages/teacher_dashboard.py")

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
            st.markdown("<div class='section-title'>Student List</div>", unsafe_allow_html=True)

            df = pd.DataFrame(students)

            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Total Students", len(df))
            with metric_col2:
                st.metric("Unique Subjects", int(df["subject"].fillna("N/A").nunique()) if "subject" in df.columns else 0)

            display_cols = [col for col in ["user_id", "name", "email", "role", "subject"] if col in df.columns]
            table_df = df[display_cols].copy() if display_cols else df.copy()

            st.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "user_id": "User ID",
                    "name": "Name",
                    "email": "Email",
                    "role": "Role",
                    "subject": "Subject",
                },
            )

            st.divider()
            st.markdown("<div class='section-title'>Open Student Profile</div>", unsafe_allow_html=True)

            student_options = {
                f"{student['user_id']} - {student['name']}": student["user_id"]
                for student in students
            }

            selected_student = st.selectbox(
                "Select a student",
                list(student_options.keys())
            )

            if st.button("👤 View Student Profile", use_container_width=True):
                st.session_state.selected_student_user_id = student_options[selected_student]
                st.switch_page("pages/teacher_student_profile.py")

        else:
            st.info("No students found.")

    else:
        try:
            st.error(response.json().get("detail", "Failed to fetch students"))
        except Exception:
            st.error("Failed to fetch students")

except requests.exceptions.ConnectionError as e:
    st.error(
        f"Cannot connect to backend at {API_BASE_URL}. "
        f"Connection error: {e}"
    )
except requests.exceptions.Timeout:
    st.error(f"Backend timeout when calling {API_BASE_URL}.")
except Exception as e:
    st.error(str(e))