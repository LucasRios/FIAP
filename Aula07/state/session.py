import streamlit as st

def init_session():

    if 'page' not in st.session_state:
        st.session_state.page = 'analysis'  # Página padrão

    if 'article' not in st.session_state:
        st.session_state.article = None  # Texto completo da notícia

    if 'summary' not in st.session_state:
        st.session_state.summary = None  # Resumo da notícia
    
    if 'sentiment' not in st.session_state:
        st.session_state.sentiment = None  # Sentimento da notícia

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "role" not in st.session_state:
        st.session_state.role = None

    if "username" not in st.session_state:
        st.session_state.username = None