# =============================================================================
# app.py — Ponto de entrada da aplicação
#
# Responsabilidade: orquestrar o roteamento entre páginas.
# Este arquivo NÃO contém lógica de negócio nem de UI detalhada.
# Ele apenas inicializa o estado e delega a renderização para cada feature.
# =============================================================================

import streamlit as st

# Configuração global da página (deve ser a 1ª chamada Streamlit)
st.set_page_config(
    page_title="AI News Analyzer",
    page_icon="📰",
    layout="wide"
)

# Módulos internos da aplicação
from state.session import init_session          # Inicializa variáveis de sessão
from ui.sidebar import render_sidebar           # Renderiza o menu lateral
from features.news_analysis import page as analysis_page
from features.history import page as history_page
from features.settings import page as settings_page

# -----------------------------------------------------------------------------
# 1. Inicializar estado da sessão (só executa se ainda não existir)
# -----------------------------------------------------------------------------
init_session()

# -----------------------------------------------------------------------------
# 2. Renderizar sidebar e capturar a página ativa
#    A sidebar retorna um identificador string, ex: "analysis"
# -----------------------------------------------------------------------------
current_page = render_sidebar()

# -----------------------------------------------------------------------------
# 3. Roteamento: chama render() da feature correspondente
# -----------------------------------------------------------------------------
if current_page == "analysis":
    analysis_page.render()

elif current_page == "history":
    history_page.render()

elif current_page == "settings":
    settings_page.render()