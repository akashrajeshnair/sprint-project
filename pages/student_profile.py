# import streamlit as st
# import requests

# # --- AUTH CHECK ---
# if "role" not in st.session_state or st.session_state.role != "student":
#     st.switch_page("streamlit_app.py")

# st.set_page_config(page_title="Student Profile", layout="centered")

# API_BASE_URL = "http://127.0.0.1:8000"

# st.title("👤 Student Profile")

# # --- BACK BUTTON ---
# if st.button("⬅ Back to Dashboard"):
#     st.switch_page("pages/student_dashboard.py")

# st.divider()

# # --- FETCH USER DATA ---
# try:
#     response = requests.get(
#         f"{API_BASE_URL}/users/by-id/{st.session_state.user_id}",
#         timeout=10
#     )

#     if response.status_code == 200:
#         user = response.json()

#         # ---------------- BASIC INFO ----------------
#         st.subheader("📌 Basic Information")

#         col1, col2 = st.columns(2)
#         with col1:
#             st.write(f"**Name:** {user.get('name', 'N/A')}")
#             st.write(f"**Email:** {user.get('email', 'N/A')}")

#         with col2:
#             st.write(f"**Role:** {user.get('role', 'N/A')}")
#             st.write(f"**Subject:** {user.get('subject', 'N/A')}")

#         st.divider()

#         # ---------------- STUDENT PROFILE ----------------
#         st.subheader("🎓 Academic Details")

#         col3, col4 = st.columns(2)
#         with col3:
#             st.write(f"**Grade Level:** {user.get('grade_level', 'N/A')}")
#             st.write(f"**Learning Style:** {user.get('learning_style', 'N/A')}")

#         with col4:
#             st.write(f"**XP Points:** {user.get('xp_points', 0)}")
#             st.write(f"**Last Active:** {user.get('last_active_at', 'N/A')}")

#         st.divider()

#         # ---------------- SUBJECTS ----------------
#         st.subheader("📚 Subjects Enrolled")

#         subjects = user.get("subjects_enrolled", [])

#         if isinstance(subjects, list) and subjects:
#             for sub in subjects:
#                 st.markdown(f"- {sub}")
#         else:
#             st.write("N/A")

#     else:
#         st.error("Failed to fetch profile details")

# except requests.exceptions.ConnectionError:
#     st.error("Backend server not running")
# except Exception as e:
#     st.error(str(e))

# import requests
# import pandas as pd
# import streamlit as st

# if "role" not in st.session_state or st.session_state.role != "student":
#     st.switch_page("streamlit_app.py")

# st.set_page_config(page_title="Student Profile", layout="wide")

# API_BASE_URL = "http://127.0.0.1:8000"

# st.title("👤 Student Profile")

# col1, col2 = st.columns(2)

# with col1:
#     if st.button("⬅ Back to Dashboard", use_container_width=True):
#         st.switch_page("pages/student_dashboard.py")

# with col2:
#     if st.button("🚪 Logout", use_container_width=True):
#         st.session_state.clear()
#         st.switch_page("streamlit_app.py")

# st.divider()

# try:
#     response = requests.get(
#         f"{API_BASE_URL}/student-profile/{st.session_state.user_id}",
#         timeout=10
#     )

#     if response.status_code == 200:
#         data = response.json()
#         user = data["user"]
#         profile = data["student_profile"]
#         progress = data["progress"]

#         st.subheader("Basic Details")
#         c1, c2 = st.columns(2)

#         with c1:
#             st.write(f"**Name:** {user.get('name', 'N/A')}")
#             st.write(f"**Email:** {user.get('email', 'N/A')}")
#             st.write(f"**Role:** {user.get('role', 'N/A')}")
#             st.write(f"**Grade Level:** {profile.get('grade_level', 'N/A')}")

#         with c2:
#             st.write(f"**Learning Style:** {profile.get('learning_style', 'N/A')}")
#             st.write(f"**Subjects Enrolled:** {', '.join(profile.get('subjects_enrolled', []))}")
#             st.write(f"**Last Active At:** {profile.get('last_active_at', 'N/A')}")

#         st.divider()

#         st.subheader("Performance Summary")
#         m1, m2, m3 = st.columns(3)

#         with m1:
#             st.metric("XP Points", profile.get("xp_points", 0))

#         with m2:
#             st.metric("Total Score", profile.get("total_score", 0))

#         with m3:
#             st.metric("Average Score", profile.get("average_score", 0))

#         st.write(f"**Topics Covered:** {profile.get('topics_covered', 0)}")

#         st.divider()

#         st.subheader("Topic-wise Progress")

#         if progress:
#             df = pd.DataFrame(progress)

#             display_df = df.copy()
#             display_df = display_df.rename(
#                 columns={
#                     "student_progress_id": "Progress ID",
#                     "subject": "Subject",
#                     "topic": "Topic",
#                     "score": "Score",
#                     "updated_at": "Updated At",
#                 }
#             )

#             st.dataframe(display_df, use_container_width=True)

#             st.divider()
#             st.subheader("Progress Graph")

#             topic_chart_df = df[["topic", "score"]].copy()
#             topic_chart_df["label"] = topic_chart_df["topic"]
#             st.write("**Score by Topic**")
#             st.bar_chart(topic_chart_df.set_index("label")["score"])

#             st.divider()
#             st.write("**Average Score by Subject**")
#             subject_chart_df = (
#                 df.groupby("subject", as_index=False)["score"]
#                 .mean()
#                 .rename(columns={"score": "average_score"})
#             )
#             st.bar_chart(subject_chart_df.set_index("subject")["average_score"])

#         else:
#             st.info("No progress records found for this student.")

#     else:
#         try:
#             st.error(response.json().get("detail", "Failed to fetch profile details"))
#         except Exception:
#             st.error("Failed to fetch profile details")

# except requests.exceptions.ConnectionError:
#     st.error("Backend server is not running.")
# except Exception as e:
#     st.error(str(e))

import os
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

if "role" not in st.session_state or st.session_state.role != "student":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="Student Profile", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 20% 20%, #1c2638 0%, #101722 48%, #0a1019 100%);
        color: #e8edf9;
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

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.title("👤 Student Profile")

col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Dashboard", use_container_width=True):
        st.switch_page("pages/student_dashboard.py")

with col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("streamlit_app.py")

st.divider()

try:
    response = requests.get(
        f"{API_BASE_URL}/student-profile/{st.session_state.user_id}",
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        user = data["user"]
        profile = data["student_profile"]
        progress = data["progress"]

        st.markdown("<div class='section-title'>Basic Details</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)

        with c1:
            with st.container(border=True):
                st.write(f"**Name:** {user.get('name', 'N/A')}")
                st.write(f"**Email:** {user.get('email', 'N/A')}")
                st.write(f"**Role:** {user.get('role', 'N/A')}")
                st.write(f"**Grade Level:** {profile.get('grade_level', 'N/A')}")

        with c2:
            with st.container(border=True):
                st.write(f"**Learning Style:** {profile.get('learning_style', 'N/A')}")
                st.write(f"**Subjects Enrolled:** {', '.join(profile.get('subjects_enrolled', []))}")
                st.write(f"**Last Active At:** {profile.get('last_active_at', 'N/A')}")

        st.divider()

        st.markdown("<div class='section-title'>Performance Summary</div>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)

        with m1:
            st.metric("XP Points", profile.get("xp_points", 0))

        with m2:
            st.metric("Total Score", profile.get("total_score", 0))

        with m3:
            st.metric("Average Score", profile.get("average_score", 0))

        st.write(f"**Topics Covered:** {profile.get('topics_covered', 0)}")

        st.divider()

        st.markdown("<div class='section-title'>Topic-wise Progress</div>", unsafe_allow_html=True)

        if progress:
            df = pd.DataFrame(progress)

            display_df = df.copy()
            display_df = display_df.rename(
                columns={
                    "student_progress_id": "Progress ID",
                    "subject": "Subject",
                    "topic": "Topic",
                    "score": "Score",
                    "updated_at": "Updated At",
                }
            )

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Score": st.column_config.ProgressColumn(
                        "Score",
                        min_value=0.0,
                        max_value=1.0,
                        format="%.2f",
                    ),
                },
            )

            st.divider()
            st.subheader("📊 Progress Visualization")

            # Score by Topic
            st.write("### 📘 Score by Topic")
            topic_df = df[["topic", "score"]].copy()

            fig1, ax1 = plt.subplots(figsize=(7, 4))
            ax1.barh(topic_df["topic"], topic_df["score"])
            ax1.set_xlabel("Score")
            ax1.set_ylabel("Topic")
            ax1.set_title("Score per Topic")
            st.pyplot(fig1)

            st.divider()

            # # Average Score by Subject
            # st.write("### 📚 Average Score by Subject")
            # subject_df = (
            #     df.groupby("subject", as_index=False)["score"]
            #     .mean()
            #     .rename(columns={"score": "average_score"})
            # )

            # fig2, ax2 = plt.subplots(figsize=(6, 4))
            # ax2.bar(subject_df["subject"], subject_df["average_score"])
            # ax2.set_xlabel("Subject")
            # ax2.set_ylabel("Average Score")
            # ax2.set_title("Average Score by Subject")
            # st.pyplot(fig2)

            # st.divider()

            # Subject-wise Pie Chart
            # st.write("### 🥧 Subject Distribution")

            # pie_data = df.groupby("subject")["score"].sum()

            # fig, ax = plt.subplots(figsize=(1, 1))  # 👈 smaller chart

            # ax.pie(
            #     pie_data,
            #     labels=pie_data.index,
            #     autopct="%1.0f%%",
            #     textprops={"fontsize": 6},   # 👈 smaller text inside & outside
            # )

            # ax.set_title("Subject Share", fontsize=6)  # 👈 smaller title

            # st.pyplot(fig)

        else:
            st.info("No progress records found for this student.")

    else:
        try:
            st.error(response.json().get("detail", "Failed to fetch profile details"))
        except Exception:
            st.error("Failed to fetch profile details")

except requests.exceptions.ConnectionError:
    st.error("Backend server is not running.")
except Exception as e:
    st.error(str(e))