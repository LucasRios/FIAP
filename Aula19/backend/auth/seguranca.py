import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

API_KEY = os.getenv("API_KEY")

def verificar_chave(chave:str = Security(api_key_header)) -> str:
    if chave !=  API_KEY:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED ,
            detail="chave inválida"
        )

    return chave