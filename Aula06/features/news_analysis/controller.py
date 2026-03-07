import streamlit as st
from pipelines.news_pipeline import analyze_news

def run_analysis():

    url = st.session_state.url_input

    result = analyze_news(
        url,
        st.session_state.model
    )

    st.session_state.article_text = result["article"]
    st.session_state.summary = result["summary"]
    st.session_state.current_url = url