import streamlit as st

@st.cache_data
def run_rag(text):

    chunks = text.split(".")[:10]

    context = " ".join(chunks)

    return context