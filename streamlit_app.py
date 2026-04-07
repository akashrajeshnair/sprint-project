import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
env_example_path = BASE_DIR / ".env.example"

if env_path.exists():
    load_dotenv(env_path)
elif env_example_path.exists():
    load_dotenv(env_example_path)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="LLM Token Tracker", page_icon="🧮", layout="centered")
st.title("LLM Token Tracker")
st.caption("Select a model name to view remaining tokens, or add a new model.")


def fetch_llms():
    response = requests.get(f"{API_BASE_URL}/llms", timeout=10)
    response.raise_for_status()
    return response.json()


def create_llm(model_name: str, total_tokens: int, tokens_used: int):
    payload = {
        "model_name": model_name,
        "total_tokens": total_tokens,
        "tokens_used": tokens_used,
    }
    response = requests.post(f"{API_BASE_URL}/llms", json=payload, timeout=10)
    return response


try:
    llm_rows = fetch_llms()
except requests.RequestException as exc:
    st.error(f"Could not fetch data from API: {exc}")
    llm_rows = []

st.subheader("Check Tokens Left")
if llm_rows:
    names = [item["model_name"] for item in llm_rows]
    selected_name = st.selectbox("Select LLM model", options=names)
    selected = next(item for item in llm_rows if item["model_name"] == selected_name)
    tokens_left = selected["total_tokens"] - selected["tokens_used"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Tokens Left", f"{tokens_left:,}")
    col2.metric("Total Tokens", f"{selected['total_tokens']:,}")
    col3.metric("Tokens Used", f"{selected['tokens_used']:,}")
else:
    st.info("No LLM records found. Add one below.")