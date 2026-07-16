# =============================================================================
# backend/main.py — Aula 19: o mesmo back-end das Aulas 15/17, agora pensado
# para rodar dentro de um container Docker.
#
# REAPROVEITADO DAS AULAS 15/17 — a única diferença de código é o host da
# aplicação, que agora precisa ser "0.0.0.0" (ver comando no Dockerfile),
# para aceitar conexões vindas de FORA do container.
#
# NENHUMA linha Python muda aqui — o que é NOVO NESTA AULA está no
# Dockerfile (backend/Dockerfile) e no docker-compose.yml, não neste arquivo.
# =============================================================================

import os
from fastapi import FastAPI, Security, HTTPException
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sprint API", version="1.3.0")

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


@app.get("/")
def raiz():
    return {"mensagem": "Sprint API rodando dentro de um container Docker"}


@app.get("/docs-info")
def docs_info():
    # Endpoint simples para o healthcheck do docker-compose (veja
    # docker-compose.yml) verificar se o container está de pé.
    return {"status": "ok"}
