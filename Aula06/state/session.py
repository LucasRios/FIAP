# =============================================================================
# state/session.py — Gerenciamento do estado global da sessão
#
# Responsabilidade: centralizar a inicialização de TODAS as variáveis de
# st.session_state. Isso evita KeyError em qualquer outro módulo que leia
# essas chaves antes de elas existirem.
#
# Regra: cada variável de estado TEM que ser declarada aqui com seu valor
# padrão. Se precisar de um novo campo, adicione aqui primeiro.
# =============================================================================

import streamlit as st

def init_session():
    """
    Inicializa as variáveis de sessão com valores padrão.

    O Streamlit mantém st.session_state entre re-renders da mesma sessão,
    mas reseta tudo ao recarregar a página. Esta função usa o padrão
    `setdefault` para não sobrescrever valores já definidos pelo usuário.
    """

    # ------------------------------------------------------------------
    # Estado da análise atual
    # ------------------------------------------------------------------
 
    if "page" not in st.session_state:
        st.session_state.page = "analysis"
    
    # ------------------------------------------------------------------
    # Histórico de análises realizadas na sessão
    # Cada item é um dicionário com: url, summary, sentiment, feedback
    # ------------------------------------------------------------------
    if "history" not in st.session_state:
        st.session_state.history = []

    # Resumo gerado pelo modelo LLM
    if "summary" not in st.session_state:
        st.session_state.summary = None

    # Resultado da análise de sentimento: dicionário com label e score
    # Ex: {"label": "Positivo", "score": 0.87, "emoji": "😊"}  
    if "sentiment" not in st.session_state:
        st.session_state.sentiment = None

    # Texto bruto extraído pelo scraper
    if "article_text" not in st.session_state:
        st.session_state.article_text = ""

    # Modelo escolhido na página de configurações 
    if "model" not in st.session_state:
        st.session_state.model = "medium"

    # Modelo escolhido na página de configurações 
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7

    # URL digitada pelo usuário (espelho do widget url_input)
    if "current_url" not in st.session_state:
        st.session_state.current_url = ""
