# =============================================================================
# backend/main.py — Aula 15: Workshop, refatorando o Sprint com FastAPI
#
# Responsabilidade: este é o back-end oficial do projeto do Sprint a partir de
# agora. Tudo que era feito dentro do Streamlit (scraping + NLP) passa a viver
# aqui, protegido por API Key e com CORS liberado só para o front-end local.
#
# NOVO NESTA AULA: a proteção por API Key (Security) combinada com CORS.
# A estrutura de app + CORS já vem das Aulas 12 e 14.
#
# Como instalar:
#   pip install fastapi uvicorn python-dotenv
#
# Como rodar:
#   uvicorn main:app --reload --port 8000
# =============================================================================

from fastapi import FastAPI, Security, HTTPException
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from routers import noticias
import os

app = FastAPI(title="Sprint API", version="1.0.0")

# -----------------------------------------------------------------------------
# SEGURANÇA — API Key — NOVO NESTA AULA
# -----------------------------------------------------------------------------
# APIKeyHeader(name="X-API-Key") diz ao FastAPI: "esperamos que o cliente
# envie um header chamado X-API-Key em toda requisição protegida".
api_key_header = APIKeyHeader(name="X-API-Key")

# A chave válida NUNCA fica escrita no código — ela vem de uma variável de
# ambiente (o arquivo .env, carregado com python-dotenv). Veja o valor padrão
# "chave-local-dev" só como fallback para você testar localmente sem .env.
API_KEY = os.getenv("API_KEY", "chave-local-dev")


def verificar_chave(chave: str = Security(api_key_header)):
    """
    Dependência de segurança: qualquer rota que declarar
    `_: str = Security(verificar_chave)` só é executada se a chave enviada
    pelo cliente bater com API_KEY. Caso contrário, o FastAPI já responde
    com 401 antes mesmo de rodar o código da rota.
    """
    if chave != API_KEY:
        raise HTTPException(status_code=401, detail="Chave inválida")
    return chave


# -----------------------------------------------------------------------------
# CORS — mesma ideia da Aula 14, agora restrita ao front-end do Sprint
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit local do Sprint
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# ROUTERS — as rotas de notícias, organizadas em módulo separado
# -----------------------------------------------------------------------------
app.include_router(noticias.router, prefix="/v1", tags=["Notícias"])


@app.get("/")
def raiz():
    return {"mensagem": "Sprint API funcionando"}
