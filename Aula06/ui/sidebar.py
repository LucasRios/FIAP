import streamlit as st

def render_sidebar():
    st.sidebar.title("AI News Analyzer")
    
    # Mapeamento Centralizado
    pages = {
        "Analisar notícia": "analysis",
        "Histórico": "history",
        "Configurações": "settings"
    }
    
    choice = st.sidebar.selectbox(
        "Navegação",
        list(pages.keys())
    )
    
    return pages[choice]