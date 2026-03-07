import streamlit as st
import time

@st.cache_data
def summarize_text(context, model):

    time.sleep(1)

    return f"Resumo gerado pelo modelo {model} baseado no conteúdo analisado."