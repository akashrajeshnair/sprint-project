import requests
import pandas as pd
import streamlit as st

if "role" not in st.session_state or st.session_state.role != "teacher":
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="Student Progress", layout="wide")

API_BASE_URL = "http://127.0.0.1:8000"

st.title("📊 Student Progress")

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
    response = requests.get(f"{API_BASE_URL}/student-progress", timeout=10)

    if response.status_code == 200:
        progress_data = response.json()

        if progress_data:
            df = pd.DataFrame(progress_data)

            if "subjects_enrolled" in df.columns:
                df["subjects_enrolled"] = df["subjects_enrolled"].apply(
                    lambda x: ", ".join(x) if isinstance(x, list) else x
                )

            st.dataframe(df, use_container_width=True)
        else:
            st.info("No student progress data found.")
    else:
        try:
            st.error(response.json().get("detail", "Failed to fetch student progress"))
        except Exception:
            st.error("Failed to fetch student progress")

except requests.exceptions.ConnectionError:
    st.error("FastAPI server is not running.")
except Exception as e:
    st.error(str(e))