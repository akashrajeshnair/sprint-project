import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Leaderboard", layout="centered")

st.title("🏆 Student Leaderboard")

try:
    response = requests.get(f"{API_BASE_URL}/students/leaderboard")

    if response.status_code == 200:
        data = response.json()

        if data:
            for i, student in enumerate(data, start=1):
                if i == 1:
                    medal = "🥇"
                elif i == 2:
                    medal = "🥈"
                elif i == 3:
                    medal = "🥉"
                else:
                    medal = f"{i}."

                st.markdown(
                    f"{medal} **{student['name']}** — {student['xp_points']} XP"
                )
        else:
            st.info("No data available")

    else:
        st.error("Failed to load leaderboard")

except Exception as e:
    st.error(str(e))