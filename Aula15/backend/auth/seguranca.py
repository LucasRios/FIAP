# =============================================================================
# auth/seguranca.py — Autenticação por API Key
#
# Toda rota protegida usa Security(verificar_chave) como dependência.
# O cliente precisa enviar o header X-API-Key com o valor correto.
# =============================================================================

import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

API_KEY = os.getenv("API_KEY", "chave-local-dev")


def verificar_chave(chave: str = Security(api_key_header)) -> str:
    """
    Dependência de segurança usada em todos os routers.
    Toda requisição precisa mandar o header X-API-Key com o valor correto.
    """
    if chave != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida.",
        )
    return chave
