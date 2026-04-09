import streamlit as st

if "role" not in st.session_state or st.session_state.role != "admin":
    st.switch_page("streamlit_app.py")

st.title("Admin Dashboard")