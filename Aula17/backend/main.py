# =============================================================================
# backend/main.py — Aula 17
#
# REAPROVEITADO DA AULA 15 (segurança por API Key + CORS). O que é NOVO
# NESTA AULA é a inclusão do router de feedback, que fecha o ciclo de
# observabilidade iniciado nas Aulas 16 e 17.
# =============================================================================

import os
from fastapi import FastAPI, Security, HTTPException
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from routers import noticias, feedback  # NOVO NESTA AULA: o router de feedback

app = FastAPI(title="Sprint API", version="1.2.0")

api_key_header = APIKeyHeader(name="X-API-Key")
API_KEY = os.getenv("API_KEY", "chave-local-dev")


def verificar_chave(chave: str = Security(api_key_header)):
    if chave != API_KEY:
        raise HTTPException(status_code=401, detail="Chave inválida")
    return chave


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(noticias.router, prefix="/v1", tags=["Notícias"])
app.include_router(feedback.router, prefix="/v1", tags=["Feedback"])  # NOVO NESTA AULA


@app.get("/")
def raiz():
    return {"mensagem": "Sprint API funcionando", "observabilidade": "LangSmith ativo"}
