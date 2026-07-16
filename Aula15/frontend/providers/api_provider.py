# =============================================================================
# frontend/providers/api_provider.py — Aula 15: front-end do Sprint refatorado
#
# Responsabilidade: substituir o antigo providers/scraper_nlp_provider.py
# (que rodava dentro do Streamlit no Semestre 1) por chamadas HTTP ao back-end
# FastAPI criado nesta aula. A interface (features/) não muda quase nada —
# só troca de onde vem o resultado.
#
# NOVO NESTA AULA: o timeout maior (30s) porque scraping + NLP pode demorar,
# e o tratamento específico para o erro 400 (nem url nem texto informados).
# =============================================================================

import requests
import streamlit as st

API_URL = st.secrets.get("API_URL", "http://localhost:8000")
API_KEY = st.secrets.get("API_KEY", "chave-local-dev")

_HEADERS = {"X-API-Key": API_KEY}


def analisar_noticia(url: str = None, texto: str = None) -> dict | None:
    """
    Chama POST /v1/noticias/analisar no back-end.

    Args:
        url: URL da notícia (opcional).
        texto: texto colado pelo usuário (opcional).
              Pelo menos um dos dois precisa ser informado.

    Returns:
        Dicionário com resumo, sentimento, entidades e confianca,
        ou None se a chamada falhar (o erro já foi exibido ao usuário).
    """
    # Montamos o payload só com os campos que realmente foram preenchidos.
    payload = {}
    if url:
        payload["url"] = url
    if texto:
        payload["texto"] = texto

    try:
        r = requests.post(
            f"{API_URL}/v1/noticias/analisar",
            json=payload,
            headers=_HEADERS,
            timeout=30,  # scraping + NLP pode ser mais lento que uma chamada simples
        )
        r.raise_for_status()  # lança uma exceção HTTPError para qualquer 4xx/5xx
        return r.json()

    except requests.HTTPError as e:
        if e.response.status_code == 400:
            st.warning("Informe uma URL ou um texto para análise.")
        elif e.response.status_code == 401:
            st.error("Erro de autenticação com o servidor.")
        else:
            st.error(f"Erro do servidor: {e.response.status_code}")

    except requests.ConnectionError:
        st.error("Não foi possível conectar ao back-end. O servidor está rodando?")

    except requests.Timeout:
        st.error("A análise está demorando mais que o esperado. Tente novamente.")

    return None
