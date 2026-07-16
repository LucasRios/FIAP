# =============================================================================
# frontend/app.py — Aula 19: front-end pensado para rodar em container Docker
#
# REAPROVEITADO DAS AULAS 13/15 — nenhuma linha Python muda aqui. O que é
# NOVO NESTA AULA é o Dockerfile (frontend/Dockerfile), que containeriza
# exatamente este mesmo app.
#
# DETALHE IMPORTANTE para quando este app roda dentro do Docker: a variável
# API_URL passa a apontar para "http://backend:8000" (o nome do serviço no
# docker-compose.yml), e não mais para "http://localhost:8000" — dentro da
# rede Docker, os containers se enxergam pelo NOME do serviço.
# =============================================================================

import streamlit as st
import requests
import os

st.set_page_config(page_title="Sprint FIAP (Docker)", page_icon="🐳", layout="wide")
st.title("Sprint FIAP — rodando em containers Docker")

# os.environ.get lê a variável de ambiente definida no docker-compose.yml
# (veja "environment: - API_URL=http://backend:8000" no compose).
# O valor padrão "http://localhost:8000" continua funcionando se você rodar
# este app fora do Docker, direto com "streamlit run app.py".
API_URL = os.environ.get("API_URL", "http://localhost:8000")

texto = st.text_area("Cole um texto para testar a conexão com o back-end:")

if st.button("Testar conexão") and texto:
    try:
        resposta = requests.get(f"{API_URL}/docs-info", timeout=5)
        st.success(f"Back-end respondeu: {resposta.json()}")
    except requests.ConnectionError:
        st.error(
            f"Não foi possível conectar em {API_URL}. "
            "Verifique se o container do back-end está no ar."
        )
