# =============================================================================
# backend/routers/noticias.py — Aula 15: endpoints de análise de notícias
#
# Responsabilidade: expor via HTTP a mesma capacidade que o Streamlit chamava
# direto no Semestre 1 (Aula 06/07) — agora protegida por API Key.
#
# NOVO NESTA AULA: os modelos Pydantic de entrada/saída e a validação manual
# "precisa vir URL OU texto" usando HTTPException.
# =============================================================================

from fastapi import APIRouter, Security, HTTPException
from pydantic import BaseModel
from pipelines.news_pipeline import processar_noticia
from main import verificar_chave

router = APIRouter()


# -----------------------------------------------------------------------------
# CONTRATOS DE ENTRADA E SAÍDA (Pydantic)
# -----------------------------------------------------------------------------
class EntradaNoticia(BaseModel):
    # "| None = None" quer dizer: este campo é OPCIONAL. O cliente pode
    # enviar url OU texto (validamos isso manualmente logo abaixo).
    url: str | None = None
    texto: str | None = None


class ResultadoNoticia(BaseModel):
    resumo: str
    sentimento: str
    entidades: list[str]
    confianca: float


# -----------------------------------------------------------------------------
# POST /v1/noticias/analisar — protegido por API Key
# -----------------------------------------------------------------------------
@router.post("/noticias/analisar", response_model=ResultadoNoticia)
def analisar_noticia(entrada: EntradaNoticia, _: str = Security(verificar_chave)):
    # Validação manual: o Pydantic já garante os TIPOS dos campos, mas a
    # regra de negócio "pelo menos um dos dois precisa vir preenchido"
    # precisamos verificar nós mesmos.
    if not entrada.url and not entrada.texto:
        raise HTTPException(status_code=400, detail="Informe url ou texto.")

    # A lógica pesada (scraping + NLP) fica isolada no pipeline — este
    # router só recebe a requisição HTTP e devolve a resposta.
    resultado = processar_noticia(url=entrada.url, texto=entrada.texto)
    return resultado


# -----------------------------------------------------------------------------
# GET /v1/noticias/historico — protegido por API Key
# -----------------------------------------------------------------------------
@router.get("/noticias/historico")
def listar_historico(_: str = Security(verificar_chave)):
    # Endpoint de exemplo: em um projeto real, retornaria dados de um banco.
    return {"analises": []}
