# =============================================================================
# frontend/app.py — Aula 15: entrada do front-end do Sprint refatorado
#
# Responsabilidade: mínima, como sempre — só configura a página e chama a
# feature. Igual ao app.py da Aula 06, trocando apenas o import da feature.
#
# Como rodar o projeto completo (2 terminais):
#
#   Terminal 1 — back-end:
#     cd backend
#     uvicorn main:app --reload --port 8000
#
#   Terminal 2 — front-end:
#     cd frontend
#     streamlit run app.py
# =============================================================================

import streamlit as st

st.set_page_config(page_title="Sprint FIAP", page_icon="📰", layout="wide")

from features.news_analysis import page as news_page

news_page.render()
