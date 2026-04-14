import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

if "role" not in st.session_state or st.session_state.role != "teacher":
    st.switch_page("streamlit_app.py")

if "selected_student_user_id" not in st.session_state:
    st.switch_page("pages/teacher_student_progress.py")

st.set_page_config(page_title="Student Profile", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 20% 20%, #1a2a22 0%, #101b16 48%, #0b120f 100%);
        color: #e8f1ea;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

API_BASE_URL = "http://127.0.0.1:8000"
student_user_id = st.session_state.selected_student_user_id

st.title("👤 Student Profile")

col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Students List", use_container_width=True):
        st.switch_page("pages/teacher_student_progress.py")

with col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("streamlit_app.py")

st.divider()

try:
    response = requests.get(
        f"{API_BASE_URL}/student-profile/{student_user_id}",
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        user = data["user"]
        profile = data["student_profile"]
        progress = data["progress"]

        st.subheader("Basic Details")
        c1, c2 = st.columns(2)

        with c1:
            st.write(f"**Name:** {user.get('name', 'N/A')}")
            st.write(f"**Email:** {user.get('email', 'N/A')}")
            st.write(f"**Role:** {user.get('role', 'N/A')}")
            st.write(f"**Grade Level:** {profile.get('grade_level', 'N/A')}")

        with c2:
            st.write(f"**Learning Style:** {profile.get('learning_style', 'N/A')}")
            st.write(f"**Subjects Enrolled:** {', '.join(profile.get('subjects_enrolled', []))}")
            st.write(f"**Last Active At:** {profile.get('last_active_at', 'N/A')}")

        st.divider()

        st.subheader("Performance Summary")
        m1, m2, m3 = st.columns(3)

        with m1:
            st.metric("XP Points", profile.get("xp_points", 0))

        with m2:
            st.metric("Total Score", profile.get("total_score", 0))

        with m3:
            st.metric("Average Score", profile.get("average_score", 0))

        st.write(f"**Topics Covered:** {profile.get('topics_covered', 0)}")

        st.divider()

        st.subheader("Topic-wise Progress")

        if progress:
            df = pd.DataFrame(progress)

            display_df = df.copy().rename(
                columns={
                    "student_progress_id": "Progress ID",
                    "subject": "Subject",
                    "topic": "Topic",
                    "score": "Score",
                    "updated_at": "Updated At",
                }
            )

            st.dataframe(display_df, use_container_width=True)

            st.divider()
            st.subheader("📊 Progress Visualization")

            st.write("### 📘 Score by Topic")
            topic_df = df[["topic", "score"]].copy()

            fig1, ax1 = plt.subplots(figsize=(7, 4))
            ax1.barh(topic_df["topic"], topic_df["score"])
            ax1.set_xlabel("Score")
            ax1.set_ylabel("Topic")
            ax1.set_title("Score per Topic", fontsize=10)
            st.pyplot(fig1)

            st.divider()
        else:
            st.info("No progress records found for this student.")

    else:
        try:
            st.error(response.json().get("detail", "Failed to fetch student profile"))
        except Exception:
            st.error("Failed to fetch student profile")

except requests.exceptions.ConnectionError:
    st.error("Backend server is not running.")
except Exception as e:
    st.error(str(e))