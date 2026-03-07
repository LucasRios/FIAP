import streamlit as st

def init_session():
    if "history" not in st.session_state:
        st.session_state.history = []

    if "article_text" not in st.session_state:
        st.session_state.article_text = None

    if "summary" not in st.session_state:
        st.session_state.summary = None

    if "current_url" not in st.session_state:
        st.session_state.current_url = None

    if "model" not in st.session_state:
        st.session_state.model = "small"  

    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.3        