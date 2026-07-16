# =============================================================================
# frontend/app.py — Ponto de entrada do front-end (Aula 13)
#
# Responsabilidade: o mais fino possível — apenas configura a página e chama
# a feature de análise. Segue o mesmo papel de "recepcionista" do app.py da
# Aula 06 do Semestre 1.
#
# IMPORTANTE — como rodar os DOIS lados ao mesmo tempo (2 terminais):
#
#   Terminal 1 (back-end, dentro da pasta Aula12/backend ou Aula13/backend):
#     uvicorn main:app --reload --port 8000
#
#   Terminal 2 (este front-end, dentro da pasta Aula13/frontend):
#     pip install streamlit requests
#     streamlit run app.py
# =============================================================================

import streamlit as st

st.set_page_config(page_title="Análise de Sentimento", page_icon="🔍", layout="wide")

from features.analise import page as analise_page

analise_page.render()
